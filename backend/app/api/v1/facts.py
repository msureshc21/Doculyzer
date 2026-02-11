"""
Company facts API endpoints.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.models import CompanyFact
from app.schemas.facts import (
    FactResponse,
    FactCreateRequest,
    FactUpdateRequest,
    FactListResponse,
    FactWithHistoryResponse,
    FactHistoryResponse,
    MissingFactsResponse
)
from app.services.prompts import get_field_definitions
from app.services.memory_graph import MemoryGraphService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/missing", response_model=MissingFactsResponse)
async def get_missing_facts(
    db: Session = Depends(get_db)
):
    """
    Get list of commonly needed facts that are missing from Memory Graph.
    
    Useful for prompting users to enter information.
    
    Args:
        db: Database session
        
    Returns:
        List of missing fact keys and suggested fields
    """
    from app.services.prompts import get_field_definitions
    
    # Get all existing facts
    existing_facts = MemoryGraphService.get_all_facts(db)
    existing_keys = {fact.fact_key for fact in existing_facts}
    
    # Get all possible fields from prompts
    field_definitions = get_field_definitions()
    all_possible_keys = {field['name'] for field in field_definitions}
    
    # Find missing facts
    missing_keys = sorted(all_possible_keys - existing_keys)
    
    # Get suggested fields with descriptions
    suggested_fields = [
        {
            "fact_key": field['name'],
            "description": field['description'],
            "type": field['type'],
            "examples": field.get('examples', [])
        }
        for field in field_definitions
        if field['name'] in missing_keys
    ]
    
    return MissingFactsResponse(
        missing_facts=missing_keys,
        suggested_fields=suggested_fields
    )


@router.get("", response_model=FactListResponse)
async def list_facts(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all active company facts.
    
    Args:
        category: Optional category filter
        db: Database session
        
    Returns:
        List of facts with total count
    """
    facts = MemoryGraphService.get_all_facts(db, category=category)
    
    return FactListResponse(
        facts=[FactResponse.model_validate(fact) for fact in facts],
        total=len(facts)
    )


@router.get("/{fact_key}", response_model=FactResponse)
async def get_fact(
    fact_key: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific fact by key.
    
    Args:
        fact_key: Key of the fact (e.g., 'company_name', 'ein')
        db: Database session
        
    Returns:
        Fact details
        
    Raises:
        HTTPException: If fact not found
    """
    fact = MemoryGraphService.get_fact(fact_key, db)
    
    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact with key '{fact_key}' not found"
        )
    
    return FactResponse.model_validate(fact)


@router.get("/{fact_key}/history", response_model=FactWithHistoryResponse)
async def get_fact_history(
    fact_key: str,
    db: Session = Depends(get_db)
):
    """
    Get a fact with its complete history.
    
    Args:
        fact_key: Key of the fact
        db: Database session
        
    Returns:
        Fact with history entries
        
    Raises:
        HTTPException: If fact not found
    """
    fact = MemoryGraphService.get_fact(fact_key, db)
    
    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fact with key '{fact_key}' not found"
        )
    
    history = MemoryGraphService.get_fact_history(fact.id, db)
    
    return FactWithHistoryResponse(
        fact=FactResponse.model_validate(fact),
        history=[FactHistoryResponse.model_validate(h) for h in history]
    )


@router.post("", response_model=FactResponse, status_code=status.HTTP_201_CREATED)
async def create_fact(
    request: FactCreateRequest,
    user_id: str = "user_anonymous",  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """
    Create a fact manually (user entry).
    
    Args:
        request: Fact creation request
        user_id: ID of the user (TODO: get from auth)
        db: Database session
        
    Returns:
        Created fact
        
    Raises:
        HTTPException: If fact already exists or creation fails
    """
    try:
        # Check if fact already exists
        existing = MemoryGraphService.get_fact(request.fact_key, db)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Fact with key '{request.fact_key}' already exists. Use PUT to update it."
            )
        
        # Create new fact manually
        from app.models import CompanyFact
        from app.models.fact_history import FactHistory, ChangeType
        from app.services.memory_graph import MemoryGraphService as MGS
        
        new_fact = CompanyFact(
            fact_key=request.fact_key,
            fact_value=request.fact_value,
            confidence=1.0,  # User-entered facts have maximum confidence
            fact_category=request.fact_category,
            last_edited_by=user_id,
            edit_count=1,
            status="active"
        )
        
        db.add(new_fact)
        db.flush()  # Get the ID
        
        # Create history entry for initial creation
        MGS._create_history_entry(
            fact=new_fact,
            change_type=ChangeType.USER_EDIT,
            old_value=None,
            new_value=request.fact_value,
            old_confidence=None,
            new_confidence="1.0",
            changed_by=user_id,
            reason="Manually entered by user",
            source_document_id=None,
            db=db
        )
        
        db.commit()
        db.refresh(new_fact)
        
        return FactResponse.model_validate(new_fact)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating fact {request.fact_key}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create fact: {str(e)}"
        )


@router.put("/{fact_key}", response_model=FactResponse)
async def update_fact(
    fact_key: str,
    request: FactUpdateRequest,
    user_id: str = "user_anonymous",  # TODO: Get from authentication
    db: Session = Depends(get_db)
):
    """
    Update a fact from a user edit.
    
    User edits always take precedence over system extractions.
    
    Args:
        fact_key: Key of the fact to update
        request: Update request with new value and optional reason
        user_id: ID of the user (TODO: get from auth)
        db: Database session
        
    Returns:
        Updated fact
        
    Raises:
        HTTPException: If fact not found or update fails
    """
    try:
        fact = MemoryGraphService.update_fact_from_user_edit(
            fact_key=fact_key,
            new_value=request.value,
            user_id=user_id,
            reason=request.reason,
            db=db
        )
        
        return FactResponse.model_validate(fact)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating fact {fact_key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update fact"
        )

