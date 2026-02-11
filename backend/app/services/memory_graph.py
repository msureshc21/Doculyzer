"""
Company Memory Graph service.

This service manages the canonical company facts (memory graph) by:
- Processing extracted fields
- Resolving conflicts between values
- Maintaining canonical values
- Tracking history and sources
- Handling user edits
"""
import logging
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import ExtractedField, CompanyFact
from app.models.fact_history import FactHistory, ChangeType

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy:
    """
    Conflict resolution strategies for handling conflicting values.
    
    Rules (in priority order):
    1. User edits always win (highest priority)
    2. Higher confidence wins
    3. If confidence difference < 0.1, newer extraction wins
    4. If same confidence and date, first extraction wins
    """
    
    CONFIDENCE_THRESHOLD = 0.1  # Minimum difference to prefer higher confidence
    
    @staticmethod
    def should_update_fact(
        existing_fact: CompanyFact,
        new_value: str,
        new_confidence: float,
        new_extraction_date
    ) -> Tuple[bool, str]:
        """
        Determine if a fact should be updated with a new value.
        
        Args:
            existing_fact: The current canonical fact
            new_value: The new extracted value
            new_confidence: Confidence of the new extraction
            new_extraction_date: Date of the new extraction
            
        Returns:
            Tuple of (should_update: bool, reason: str)
        """
        # Rule 1: User edits always win - never overwrite user-edited facts
        if existing_fact.edit_count > 0:
            return False, "Fact has been user-edited, preserving user value"
        
        # Rule 2: If values are identical (normalized), no update needed
        if _normalize_value(existing_fact.fact_value) == _normalize_value(new_value):
            return False, "Values are identical (normalized)"
        
        # Rule 3: Higher confidence wins
        confidence_diff = new_confidence - existing_fact.confidence
        
        if confidence_diff > ConflictResolutionStrategy.CONFIDENCE_THRESHOLD:
            return True, f"New value has significantly higher confidence ({new_confidence:.2f} vs {existing_fact.confidence:.2f})"
        
        if confidence_diff < -ConflictResolutionStrategy.CONFIDENCE_THRESHOLD:
            return False, f"Existing value has significantly higher confidence ({existing_fact.confidence:.2f} vs {new_confidence:.2f})"
        
        # Rule 4: If confidence is similar, newer extraction wins
        if new_extraction_date > existing_fact.updated_at:
            return True, f"Confidence similar, newer extraction wins ({new_confidence:.2f} vs {existing_fact.confidence:.2f})"
        
        return False, f"Confidence similar, existing value is newer ({existing_fact.confidence:.2f} vs {new_confidence:.2f})"


def _normalize_value(value: str) -> str:
    """
    Normalize a value for comparison.
    
    Args:
        value: The value to normalize
        
    Returns:
        Normalized value (lowercase, stripped, etc.)
    """
    if not value:
        return ""
    return value.lower().strip()


def _get_fact_category(field_name: str) -> str:
    """
    Determine fact category from field name.
    
    Args:
        field_name: Name of the field
        
    Returns:
        Category string
    """
    # Categorize fields
    if field_name in ['company_name', 'dba_name']:
        return 'company_info'
    elif field_name in ['ein', 'tax_id']:
        return 'legal'
    elif field_name.startswith('address'):
        return 'location'
    elif field_name in ['phone', 'email', 'website']:
        return 'contact'
    elif 'incorporation' in field_name or 'date' in field_name:
        return 'legal'
    else:
        return 'company_info'


class MemoryGraphService:
    """
    Service for managing the Company Memory Graph.
    
    This service processes extracted fields and maintains canonical facts
    with conflict resolution and history tracking.
    """
    
    @staticmethod
    def process_extracted_fields(
        document_id: int,
        db: Session
    ) -> List[CompanyFact]:
        """
        Process extracted fields from a document and update the memory graph.
        
        Args:
            document_id: ID of the document
            db: Database session
            
        Returns:
            List of created/updated CompanyFact records
        """
        logger.info(f"Processing extracted fields for document {document_id}")
        
        # Get all extracted fields for this document
        extracted_fields = db.query(ExtractedField).filter(
            ExtractedField.document_id == document_id
        ).all()
        
        if not extracted_fields:
            logger.info(f"No extracted fields found for document {document_id}")
            return []
        
        processed_facts = []
        
        # Group by field_name to handle multiple extractions of same field
        field_groups = {}
        for field in extracted_fields:
            if field.field_name not in field_groups:
                field_groups[field.field_name] = []
            field_groups[field.field_name].append(field)
        
        # Process each field
        for field_name, fields in field_groups.items():
            # For each field, pick the best extraction (highest confidence)
            best_field = max(fields, key=lambda f: f.confidence)
            
            try:
                fact = MemoryGraphService._process_single_field(
                    field_name=field_name,
                    extracted_field=best_field,
                    db=db
                )
                if fact:
                    processed_facts.append(fact)
            except Exception as e:
                logger.error(f"Error processing field {field_name}: {e}")
                continue
        
        db.commit()
        logger.info(f"Processed {len(processed_facts)} facts for document {document_id}")
        
        return processed_facts
    
    @staticmethod
    def _process_single_field(
        field_name: str,
        extracted_field: ExtractedField,
        db: Session
    ) -> Optional[CompanyFact]:
        """
        Process a single extracted field and create/update canonical fact.
        
        Args:
            field_name: Name of the field
            extracted_field: The extracted field record
            db: Database session
            
        Returns:
            Created or updated CompanyFact, or None if no update needed
        """
        # Check if fact already exists
        existing_fact = db.query(CompanyFact).filter(
            CompanyFact.fact_key == field_name,
            CompanyFact.status == "active"
        ).first()
        
        if existing_fact:
            # Resolve conflict
            should_update, reason = ConflictResolutionStrategy.should_update_fact(
                existing_fact=existing_fact,
                new_value=extracted_field.value,
                new_confidence=extracted_field.confidence,
                new_extraction_date=extracted_field.extraction_date
            )
            
            if should_update:
                # Update existing fact
                old_value = existing_fact.fact_value
                old_confidence = existing_fact.confidence
                
                existing_fact.fact_value = extracted_field.value
                existing_fact.confidence = extracted_field.confidence
                existing_fact.source_document_id = extracted_field.document_id
                existing_fact.source_field_id = extracted_field.id
                existing_fact.fact_category = _get_fact_category(field_name)
                
                # Create history entry
                MemoryGraphService._create_history_entry(
                    fact=existing_fact,
                    change_type=ChangeType.SYSTEM_UPDATE,
                    old_value=old_value,
                    new_value=extracted_field.value,
                    old_confidence=str(old_confidence),
                    new_confidence=str(extracted_field.confidence),
                    changed_by="system",
                    reason=reason,
                    source_document_id=extracted_field.document_id,
                    db=db
                )
                
                logger.info(f"Updated fact {field_name}: {reason}")
                return existing_fact
            else:
                logger.info(f"Skipped update for {field_name}: {reason}")
                # Still create history entry for the attempt
                MemoryGraphService._create_history_entry(
                    fact=existing_fact,
                    change_type=ChangeType.EXTRACTION,
                    old_value=existing_fact.fact_value,
                    new_value=extracted_field.value,
                    old_confidence=str(existing_fact.confidence),
                    new_confidence=str(extracted_field.confidence),
                    changed_by="system",
                    reason=f"Extraction attempted but not applied: {reason}",
                    source_document_id=extracted_field.document_id,
                    db=db
                )
                return None
        else:
            # Create new fact
            new_fact = CompanyFact(
                fact_key=field_name,
                fact_value=extracted_field.value,
                confidence=extracted_field.confidence,
                fact_category=_get_fact_category(field_name),
                source_document_id=extracted_field.document_id,
                source_field_id=extracted_field.id,
                last_edited_by="system",
                status="active"
            )
            
            db.add(new_fact)
            db.flush()  # Get the ID
            
            # Create history entry for initial creation
            MemoryGraphService._create_history_entry(
                fact=new_fact,
                change_type=ChangeType.EXTRACTION,
                old_value=None,
                new_value=extracted_field.value,
                old_confidence=None,
                new_confidence=str(extracted_field.confidence),
                changed_by="system",
                reason="Initial extraction from document",
                source_document_id=extracted_field.document_id,
                db=db
            )
            
            logger.info(f"Created new fact {field_name}: {extracted_field.value}")
            return new_fact
    
    @staticmethod
    def _create_history_entry(
        fact: CompanyFact,
        change_type: ChangeType,
        old_value: Optional[str],
        new_value: str,
        old_confidence: Optional[str],
        new_confidence: Optional[str],
        changed_by: str,
        reason: Optional[str],
        source_document_id: Optional[int],
        db: Session
    ) -> FactHistory:
        """
        Create a history entry for a fact change.
        
        Args:
            fact: The CompanyFact that changed
            change_type: Type of change
            old_value: Previous value (None for creation)
            new_value: New value
            old_confidence: Previous confidence
            new_confidence: New confidence
            changed_by: Who made the change
            reason: Reason for the change
            source_document_id: Source document if applicable
            db: Database session
            
        Returns:
            Created FactHistory record
        """
        history_entry = FactHistory(
            fact_id=fact.id,
            change_type=change_type,
            changed_by=changed_by,
            old_value=old_value,
            new_value=new_value,
            old_confidence=old_confidence,
            new_confidence=new_confidence,
            reason=reason,
            source_document_id=source_document_id
        )
        
        db.add(history_entry)
        return history_entry
    
    @staticmethod
    def update_fact_from_user_edit(
        fact_key: str,
        new_value: str,
        user_id: str,
        reason: Optional[str],
        db: Session
    ) -> CompanyFact:
        """
        Update a fact from a user edit.
        
        User edits always take precedence over system extractions.
        
        Args:
            fact_key: Key of the fact to update
            new_value: New value from user
            user_id: ID of the user making the edit
            reason: Optional reason for the edit
            db: Database session
            
        Returns:
            Updated CompanyFact
            
        Raises:
            ValueError: If fact not found
        """
        fact = db.query(CompanyFact).filter(
            CompanyFact.fact_key == fact_key,
            CompanyFact.status == "active"
        ).first()
        
        if not fact:
            raise ValueError(f"Fact with key '{fact_key}' not found")
        
        # Check if value actually changed
        if _normalize_value(fact.fact_value) == _normalize_value(new_value):
            logger.info(f"User edit for {fact_key}: value unchanged, skipping update")
            return fact
        
        old_value = fact.fact_value
        old_confidence = str(fact.confidence)
        
        # Update fact
        fact.fact_value = new_value
        fact.confidence = 1.0  # User edits have maximum confidence
        fact.last_edited_by = user_id
        fact.edit_count += 1
        
        # Create history entry
        MemoryGraphService._create_history_entry(
            fact=fact,
            change_type=ChangeType.USER_EDIT,
            old_value=old_value,
            new_value=new_value,
            old_confidence=old_confidence,
            new_confidence="1.0",
            changed_by=user_id,
            reason=reason or "User edit",
            source_document_id=None,
            db=db
        )
        
        db.commit()
        logger.info(f"User {user_id} edited fact {fact_key}: {old_value} -> {new_value}")
        
        return fact
    
    @staticmethod
    def get_fact(fact_key: str, db: Session) -> Optional[CompanyFact]:
        """
        Get a canonical fact by key.
        
        Args:
            fact_key: Key of the fact
            db: Database session
            
        Returns:
            CompanyFact or None if not found
        """
        return db.query(CompanyFact).filter(
            CompanyFact.fact_key == fact_key,
            CompanyFact.status == "active"
        ).first()
    
    @staticmethod
    def get_all_facts(db: Session, category: Optional[str] = None) -> List[CompanyFact]:
        """
        Get all active canonical facts.
        
        Args:
            db: Database session
            category: Optional category filter
            
        Returns:
            List of CompanyFact records
        """
        query = db.query(CompanyFact).filter(CompanyFact.status == "active")
        
        if category:
            query = query.filter(CompanyFact.fact_category == category)
        
        return query.all()
    
    @staticmethod
    def get_fact_history(fact_id: int, db: Session) -> List[FactHistory]:
        """
        Get history for a fact.
        
        Args:
            fact_id: ID of the fact
            db: Database session
            
        Returns:
            List of FactHistory records (newest first)
        """
        return db.query(FactHistory).filter(
            FactHistory.fact_id == fact_id
        ).order_by(FactHistory.changed_at.desc()).all()

