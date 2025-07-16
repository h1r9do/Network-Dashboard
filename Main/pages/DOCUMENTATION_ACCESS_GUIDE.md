# DSR Circuits - Documentation Access Guide

## How to Access Documentation

### Web-Based Access (Recommended)

All documentation files are now accessible through the web interface using the `/docs/` endpoint.

#### Accessing Documentation Online:

1. **Main README**:
   - URL: `http://neamsatcor1ld01.trtc.com:5052/readme`
   - This provides the main system overview and links to all other documentation

2. **Individual Documentation Files**:
   - Pattern: `http://neamsatcor1ld01.trtc.com:5052/docs/[filename].md`
   - Example: `http://neamsatcor1ld01.trtc.com:5052/docs/HOME_PAGE.md`

#### Available Documentation URLs:

##### Web Interface Guides
- **Home Page Guide**: http://neamsatcor1ld01.trtc.com:5052/docs/HOME_PAGE.md
- **Dashboard Guide**: http://neamsatcor1ld01.trtc.com:5052/docs/DSR_DASHBOARD.md
- **New Stores Guide**: http://neamsatcor1ld01.trtc.com:5052/docs/NEW_STORES.md

##### Technical Documentation
- **Nightly Scripts**: http://neamsatcor1ld01.trtc.com:5052/docs/NIGHTLY_SCRIPTS.md
- **Flask Scripts**: http://neamsatcor1ld01.trtc.com:5052/docs/FLASK_SCRIPTS.md
- **Primary Key Analysis**: http://neamsatcor1ld01.trtc.com:5052/docs/PRIMARY_KEY_ANALYSIS.md

##### Additional Reports
- **README Verification**: http://neamsatcor1ld01.trtc.com:5052/docs/README_VERIFICATION.md
- **URL Validation Report**: http://neamsatcor1ld01.trtc.com:5052/docs/URL_VALIDATION_REPORT.md

### How the Documentation System Works

1. **Markdown Rendering**:
   - The Flask application converts .md files to HTML
   - Supports tables, code highlighting, and formatting
   - Wrapped in the DSR Circuits template for consistent styling

2. **File Locations**:
   - Documentation files are stored in `/usr/local/bin/Main/pages/`
   - The `/docs/` route automatically finds and serves these files
   - Files must have `.md` extension

3. **Security**:
   - Only `.md` files can be accessed through the `/docs/` route
   - Path traversal attacks are prevented
   - Files outside designated directories cannot be accessed

### Local File Access

For system administrators who need direct file access:

```bash
# View documentation files locally
cd /usr/local/bin/Main/pages/
ls -la *.md

# Read a specific file
cat HOME_PAGE.md

# Edit documentation
vim NIGHTLY_SCRIPTS.md
```

### Adding New Documentation

To add new documentation:

1. Create a new `.md` file in `/usr/local/bin/Main/pages/`
2. Use standard Markdown formatting
3. Access it immediately at: `http://neamsatcor1ld01.trtc.com:5052/docs/YOUR_FILE.md`

### Documentation Standards

- Use descriptive filenames (e.g., `FEATURE_NAME.md`)
- Start with a clear H1 header
- Include overview, details, and examples
- Use code blocks for technical content
- Keep formatting consistent with existing docs

---
*Last Updated: July 3, 2025*  
*Part of DSR Circuits Documentation Suite*