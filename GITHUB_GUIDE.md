# 🚀 How to Upload Your Project to GitHub

Since **Git** is not installed on your computer yet, you'll need to follow these steps.

## Step 1: Install Git
1.  Go to the official Git website: [https://git-scm.com/download/win](https://git-scm.com/download/win)
2.  Click on **"Click here to download"** to get the installer.
3.  Run the installer and just click **"Next"** through all the options (the defaults are fine).
4.  **Important**: Once installed, **restart your computer** or close and reopen VS Code for it to work.

## Step 2: Create a Repository on GitHub
1.  Log in to [GitHub.com](https://github.com).
2.  Click the **+** icon in the top-right corner and select **"New repository"**.
3.  **Repository name**: `PartnerAI` (or whatever you like).
4.  **Public/Private**: Choose whichever you prefer.
5.  **Do NOT check** "Add a README", "Add .gitignore", or "Add a license" (we already made these files locally).
6.  Click **Create repository**.

## Step 3: Connect and Push
Once you have created the repo, GitHub will show you a page with commands.

**Open a new Terminal** in this folder (VS Code: Terminal > New Terminal) and copy-paste these commands one by one:

```powershell
# 1. Initialize Git in your folder
git init

# 2. Add all your files
git add .

# 3. Commit your changes
git commit -m "First commit: PartnerAI initial setup"

# 4. Rename the branch to 'main'
git branch -M main

# 5. Connect to your new GitHub repo
# REPLACE 'YOUR_USERNAME' WITH YOUR ACTUAL GITHUB USERNAME!
git remote add origin https://github.com/YOUR_USERNAME/PartnerAI.git

# 6. Upload your code
git push -u origin main
```

## 🎉 Done!
Your code is now on GitHub.
