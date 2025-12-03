# Deployment Guide for Digital Sufism Website

This guide will walk you through deploying your Quarto website to GitHub Pages at `https://digitalsufism.github.io/`.

## Prerequisites

- GitHub account (you're logged in as zurstadt)
- Quarto installed on your computer
- Git installed on your computer
- Terminal/command line access

## Step-by-Step Deployment Process

### Phase 1: Create GitHub Organization (5 minutes)

1. **Go to GitHub** and log in as zurstadt
   - Visit: https://github.com

2. **Create new organization**
   - Click your profile photo (top-right)
   - Select "Your organizations"
   - Click "New organization"
   - Choose "Create a free organization"

3. **Configure organization**
   - Organization account name: `digitalsufism`
   - Contact email: (your email)
   - This organization belongs to: "My personal account"
   - Click "Next"
   - Skip the team members step (click "Complete setup")

### Phase 2: Create Repository (3 minutes)

1. **Create new repository** in digitalsufism organization
   - From the organization page, click "Create a new repository"
   - Or visit: https://github.com/organizations/digitalsufism/repositories/new

2. **Configure repository**
   - Repository name: **EXACTLY** `digitalsufism.github.io`
   - Description: "Digital Sufism project - materials for the study of early Sufism"
   - Visibility: **Public** (required for free GitHub Pages)
   - Do NOT check "Add a README file"
   - Do NOT check "Add .gitignore"
   - Do NOT choose a license
   - Click "Create repository"

3. **Note the repository URL**
   - You should see: `https://github.com/digitalsufism/digitalsufism.github.io`
   - Keep this page open for reference

### Phase 3: Push Your Site to GitHub (5 minutes)

Open Terminal and navigate to your project:

```bash
cd /Users/jfireland05/Desktop/git-projects/digital-sufism/quarto-digitalsufism
```

Initialize Git and push:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Quarto Digital Sufism website"

# Connect to GitHub repository
git remote add origin https://github.com/digitalsufism/digitalsufism.github.io.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

**Note**: You may be prompted for your GitHub username and password. For password, use a [Personal Access Token](https://github.com/settings/tokens) rather than your actual password.

### Phase 4: Create gh-pages Branch (2 minutes)

This branch will hold your published website:

```bash
# Create empty gh-pages branch
git checkout --orphan gh-pages
git reset --hard
git commit --allow-empty -m "Initialize gh-pages branch"
git push origin gh-pages

# Switch back to main branch
git checkout main
```

### Phase 5: Configure GitHub Pages (2 minutes)

1. **Go to repository settings**
   - Visit: https://github.com/digitalsufism/digitalsufism.github.io/settings/pages

2. **Configure Pages**
   - Under "Source", select:
     - Branch: `gh-pages`
     - Folder: `/ (root)`
   - Click "Save"

3. **Note**: GitHub will show the URL where your site will be published: `https://digitalsufism.github.io/`

### Phase 6: Publish Your Site (1 minute)

From your project directory:

```bash
quarto publish gh-pages
```

You'll see output like:
```
? Update site at https://digitalsufism.github.io/? (Y/n) ›
```

Press `Y` and Enter.

Quarto will:
1. Render all your pages
2. Push the content to the gh-pages branch
3. Your site will go live!

**Wait 1-2 minutes**, then visit: **https://digitalsufism.github.io/**

🎉 Your site is live!

## Future Updates

### Making Changes

1. **Edit your files** in the `quarto-digitalsufism` directory
   - Modify .qmd files for content
   - Update `data/bibliography.json` to add more works
   - Edit `custom.scss` for styling changes

2. **Preview changes locally**
   ```bash
   quarto preview
   ```
   Visit http://localhost:4444 to see your changes

3. **Commit changes to Git**
   ```bash
   git add .
   git commit -m "Description of your changes"
   git push
   ```

4. **Publish to GitHub Pages**
   ```bash
   quarto publish gh-pages
   ```

### Adding More Bibliography Entries

The current `data/bibliography.json` has sample entries. To add more:

1. Open `data/bibliography.json` in a text editor
2. Add new author objects or works following the existing structure
3. Each work should have:
   - Unique `id`
   - `title` (Arabic)
   - `type`: one of `discursive`, `isnad`, `reconstruction`, `uncertain`
   - Arrays for `editions`, `translations`, `manuscripts`, `reproductions`
4. Save the file
5. Test locally with `quarto preview`
6. Commit and publish

### Maintaining Two Sites

If you want to keep both zurstadt.github.io and digitalsufism.github.io:

- **zurstadt.github.io**: Your personal academic site
- **digitalsufism.github.io**: The Digital Sufism project

They're independent and can coexist!

## Troubleshooting

### Issue: "Repository already exists"
- Someone else may have created `digitalsufism` organization
- Try a variation like `digitalsufism-project`
- Update `_quarto.yml` with the new URL

### Issue: "gh-pages branch not found"
- Make sure you created and pushed the gh-pages branch (Phase 4)
- Check branches: `git branch -a`

### Issue: "Site not updating"
- Wait 2-3 minutes after publishing
- Check GitHub Actions: https://github.com/digitalsufism/digitalsufism.github.io/actions
- Clear browser cache or try incognito mode

### Issue: "404 when visiting site"
- Verify GitHub Pages is configured correctly in Settings → Pages
- Ensure `gh-pages` branch exists
- Wait a few minutes for DNS propagation

### Issue: Authentication failed when pushing
- Use a [Personal Access Token](https://github.com/settings/tokens) instead of password
- Or set up [SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

## Advanced: Custom Domain (Optional)

If you want to use a custom domain like `digitalsufism.org`:

1. Purchase domain from a registrar
2. Add `CNAME` file to your project root:
   ```
   digitalsufism.org
   ```
3. Configure DNS with your registrar:
   - Add `CNAME` record pointing to `digitalsufism.github.io`
4. In GitHub Settings → Pages, add your custom domain
5. Enable "Enforce HTTPS"

## Support

- **Quarto Documentation**: https://quarto.org/docs/publishing/github-pages.html
- **GitHub Pages Docs**: https://docs.github.com/en/pages
- **Project Issues**: Open an issue on GitHub if you encounter problems

## Next Steps

1. ✅ Complete the deployment following this guide
2. Add more bibliography entries to `data/bibliography.json`
3. Develop content for Secondary Scholarship page
4. Develop content for Future Directions page
5. Set up blog posts when ready
6. Share your new site URL with colleagues!

---

**Your new site will be live at**: https://digitalsufism.github.io/

Good luck! 🚀
