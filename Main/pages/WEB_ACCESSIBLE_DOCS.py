"""
Add this code to dsrcircuits.py to make pages documentation web-accessible
"""

# Add these routes after the existing documentation routes (around line 990)

@app.route('/documentation')
def documentation_index():
    """Documentation index page listing all available docs"""
    import os
    
    # Get list of documentation files from pages directory
    pages_dir = '/usr/local/bin/Main/pages'
    doc_files = []
    
    if os.path.exists(pages_dir):
        for filename in os.listdir(pages_dir):
            if filename.endswith('.md'):
                doc_files.append({
                    'name': filename.replace('.md', '').replace('_', ' ').title(),
                    'filename': filename,
                    'path': f'pages/{filename}'
                })
    
    # Sort by name
    doc_files.sort(key=lambda x: x['name'])
    
    return render_template('documentation_index.html', documents=doc_files)

@app.route('/docs/pages/<filename>')
def serve_page_documentation(filename):
    """Serve documentation files from pages directory"""
    try:
        import markdown
        import os
        
        # Security check - only allow .md files
        if not filename.endswith('.md'):
            return abort(404)
        
        # Construct safe file path
        file_path = os.path.join('/usr/local/bin/Main/pages', filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            return abort(404)
        
        # Read and convert markdown to HTML
        with open(file_path, 'r') as f:
            content = f.read()
        
        html_content = markdown.markdown(
            content,
            extensions=['extra', 'codehilite', 'nl2br', 'toc', 'tables']
        )
        
        # Get document title from first line
        lines = content.split('\n')
        title = 'Documentation'
        for line in lines:
            if line.strip().startswith('#'):
                title = line.strip('#').strip()
                break
        
        # Return as JSON for AJAX loading or render template
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'title': title,
                'content': html_content
            })
        else:
            return render_template('documentation_viewer.html', 
                                 title=title, 
                                 content=html_content,
                                 filename=filename)
    
    except Exception as e:
        return f'Error loading documentation: {str(e)}', 500

# API endpoint to list all documentation
@app.route('/api/documentation/list')
def list_documentation():
    """API endpoint to list all available documentation files"""
    import os
    
    docs = []
    
    # Main documentation
    if os.path.exists('/usr/local/bin/Main/README.md'):
        docs.append({
            'category': 'Main',
            'name': 'README',
            'path': 'README.md',
            'url': '/readme'
        })
    
    # Pages documentation
    pages_dir = '/usr/local/bin/Main/pages'
    if os.path.exists(pages_dir):
        for filename in os.listdir(pages_dir):
            if filename.endswith('.md'):
                docs.append({
                    'category': 'Pages',
                    'name': filename.replace('.md', '').replace('_', ' ').title(),
                    'path': f'pages/{filename}',
                    'url': f'/docs/pages/{filename}'
                })
    
    return jsonify(docs)