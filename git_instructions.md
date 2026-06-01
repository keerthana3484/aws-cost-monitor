# Git & GitHub Instructions Guide

This guide explains how your project is linked to GitHub and how you can track and push your changes in the future.

---

## 1. Quick Setup Reference (If Git command is not recognized)
If you open a new terminal and the command `git` is not recognized, run this command in PowerShell to load Git into your active session:
```powershell
$env:Path += ";C:\Program Files\Git\cmd"
```

---

## 2. Daily Commands (How to push new updates)
Whenever you make changes to your project and want to save them to GitHub, run these three commands in your terminal:

### Step A: Stage your changes
This prepares all modified or new files to be saved.
```powershell
git add .
```

### Step B: Save your changes locally
This creates a local checkpoint (commit) describing what you did.
```powershell
git commit -m "Describe what changes you made"
```

### Step C: Push your changes to GitHub
This uploads your local checkpoint to your GitHub repository.
```powershell
git push
```

---

## 3. Useful Commands
* **Check Status**: See which files have been modified or are untracked.
  ```powershell
  git status
  ```
* **View Commit History**: See a list of your past commits.
  ```powershell
  git log --oneline
  ```
