# Digital Sufism / التصوّف الرقميّ

A Quarto-based website for materials on the study of early Sufism (3rd/9th-4th/10th centuries) in digital format.

## Features

- **Interactive Bibliography Database**: Searchable, filterable collection of 149 primary source works by 32 early Sufi authors
- **Observable JS Interface**: Real-time client-side filtering and search
- **Dark Theme**: Custom styling optimized for academic content
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Google Analytics Integration**: Track site usage

## Local Development

### Prerequisites

- [Quarto](https://quarto.org/docs/get-started/) (version 1.3 or later)
- A modern web browser

### Running Locally

1. Clone this repository
2. Navigate to the project directory
3. Run the preview server:

```bash
quarto preview
```

4. Open your browser to `http://localhost:####` (port will be shown in terminal)

### Building the Site

To render the complete site:

```bash
quarto render
```

The rendered site will be in the `_site/` directory.

## Deployment to GitHub Pages

### Step 1: Create GitHub Organization

1. Go to https://github.com and log in
2. Click your profile photo → "Your organizations" → "New organization"
3. Choose "Create a free organization"
4. Organization name: `digitalsufism`
5. Create the organization

### Step 2: Create Repository

1. In the digitalsufism organization, create a new repository
2. Repository name: **MUST BE** `digitalsufism.github.io` (exactly this)
3. Make it public
4. Do NOT initialize with README (we'll push our code)

### Step 3: Initialize Git and Push

From the project directory:

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit of Quarto Digital Sufism site"

# Add remote (replace with your org's repo)
git remote add origin https://github.com/digitalsufism/digitalsufism.github.io.git

# Push to main branch
git branch -M main
git push -u origin main
```

### Step 4: Set Up GitHub Pages Branch

```bash
# Create orphan gh-pages branch
git checkout --orphan gh-pages
git reset --hard
git commit --allow-empty -m "Initialize gh-pages branch"
git push origin gh-pages

# Switch back to main
git checkout main
```

### Step 5: Configure GitHub Pages

1. Go to repository Settings → Pages
2. Under "Source", select branch: `gh-pages`
3. Select folder: `/` (root)
4. Click Save

### Step 6: Publish

From the project directory on the main branch:

```bash
quarto publish gh-pages
```

This command will:
- Render your site
- Push the rendered content to the `gh-pages` branch
- Your site will be live at `https://digitalsufism.github.io/` in a few minutes!

### Updating the Site

After making changes:

```bash
# Commit your changes to main
git add .
git commit -m "Description of changes"
git push

# Publish to GitHub Pages
quarto publish gh-pages
```

## Project Structure

```
quarto-digitalsufism/
├── _quarto.yml           # Site configuration
├── custom.scss           # Custom styling
├── index.qmd             # Home page
├── primary.qmd           # Interactive bibliography
├── secondary.qmd         # Secondary scholarship
├── futuredirections.qmd  # Future directions
├── blog.qmd              # Blog (placeholder)
├── cv.qmd                # CV page
├── data/
│   └── bibliography.json # Bibliography database
└── img/
    └── sufi.png          # Logo and images
```

## Bibliography Data

The bibliography is stored in `data/bibliography.json`. To add more entries:

1. Open `data/bibliography.json`
2. Follow the existing structure for authors and works
3. Each work should include:
   - `id`: Unique identifier
   - `title`: Arabic title
   - `type`: One of `discursive`, `isnad`, `reconstruction`, `uncertain`
   - `editions`: Array of edition objects with `citation` and optional `link`
   - `translations`: Array of translation objects
   - `manuscripts`: Array of manuscript references
   - `reproductions`: Array of reproduction references

## License

Content is licensed under **Attribution-NonCommercial – CC BY-NC**.

© 2019–2025 Jeremy Farrell

## Contact

- Email: digitalsufism@gmail.com
- GitHub: https://github.com/digitalsufism
- Academia.edu: https://emory.academia.edu/JeremyFarrell
