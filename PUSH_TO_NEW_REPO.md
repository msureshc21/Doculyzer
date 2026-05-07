# Push This Project to a New GitHub Repository

The old remote has been removed. Follow these steps to create a new repo and push.

## 1. Create the new repository on GitHub

1. Go to **https://github.com/new**
2. Sign in if needed.
3. Set **Repository name** (e.g. `Doculyzer` or `ProjectParaLegal`).
4. Choose **Public** (or Private).
5. **Do not** add a README, .gitignore, or license (this project already has them).
6. Click **Create repository**.

## 2. Add the new remote and push

In Terminal, from this project folder, run (replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your GitHub username and the repo name you chose):

```bash
cd /Users/msc/Documents/ProjectParaLegal

# Add your new repo as origin (use the URL GitHub shows on the new repo page)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Push your code
git push -u origin main
```

**Example** if your username is `msureshc21` and repo name is `Doculyzer`:

```bash
git remote add origin https://github.com/msureshc21/Doculyzer.git
git push -u origin main
```

When prompted for credentials, use your GitHub username and a [Personal Access Token](https://github.com/settings/tokens) (with `repo` scope) as the password.

**Using SSH instead:** if you use SSH keys with GitHub, use:

```bash
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```
