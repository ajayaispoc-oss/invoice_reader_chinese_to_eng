# 1. Initialize a blank local Git repository context tracker
git init

git config --global user.email "ajay.ai.spoc@gmail.com"
git config --global user.name "ajayaispoc-oss"

# 2. Force branch synchronization configuration context to 'main'
git branch -M main

# 3. Stage all source scripts, local modules, and requirement matrices
git add .

# 4. Commit the clean components state to your local branch validation tree
git commit -m "Initial commit: Intelligent Content-Based Chinese Invoice OCR Router pipeline"
# 5. Connect your local branch tracker to your new remote GitHub target asset location
git remote add origin https://github.com/ajayaispoc-oss/invoice_reader_chinese_to_eng.git

# 6. Execute the secure push, linking local master streams straight to remote origin main
git push -u origin main
