#!/usr/bin/env python3
"""
Script to convert Workflow Studio Architecture Documentation to HTML format
for easy copying into Google Docs.
"""

import markdown
import re
from pathlib import Path

def convert_markdown_to_html(markdown_file, output_file):
    """Convert markdown file to HTML format suitable for Google Docs."""
    
    # Read the markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Configure markdown extensions for better HTML output
    extensions = [
        'markdown.extensions.tables',
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br'
    ]
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_content, extensions=extensions)
    
    # Add CSS styling for better appearance in Google Docs
    css_styles = """
    <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
    h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
    h2 { color: #34495e; border-bottom: 1px solid #bdc3c7; padding-bottom: 5px; }
    h3 { color: #7f8c8d; }
    h4 { color: #95a5a6; }
    code { background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; font-family: 'Courier New', monospace; }
    pre { background-color: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }
    pre code { background-color: transparent; padding: 0; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; font-weight: bold; }
    blockquote { border-left: 4px solid #3498db; margin: 0; padding-left: 15px; color: #7f8c8d; }
    .emoji { font-size: 1.2em; }
    </style>
    """
    
    # Create the complete HTML document
    html_document = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Workflow Studio - Complete Architecture Documentation</title>
        {css_styles}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_document)
    
    print(f"✅ Successfully converted {markdown_file} to {output_file}")
    print(f"📄 You can now open {output_file} in your browser and copy the content to Google Docs")

def create_plain_text_version(markdown_file, output_file):
    """Create a plain text version for easy copying."""
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove markdown formatting but keep structure
    # Convert headers
    content = re.sub(r'^#+\s+(.+)$', r'\1', content, flags=re.MULTILINE)
    
    # Convert code blocks
    content = re.sub(r'```[\w]*\n(.*?)\n```', r'\1', content, flags=re.DOTALL)
    
    # Convert inline code
    content = re.sub(r'`([^`]+)`', r'\1', content)
    
    # Convert bold and italic
    content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
    content = re.sub(r'\*(.+?)\*', r'\1', content)
    
    # Convert links
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
    
    # Convert tables to simple format
    content = re.sub(r'\|(.+)\|', r'\1', content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"📝 Created plain text version: {output_file}")

if __name__ == "__main__":
    # Convert the architecture documentation
    markdown_file = "ARCHITECTURE_DOCUMENTATION.md"
    html_file = "ARCHITECTURE_DOCUMENTATION.html"
    text_file = "ARCHITECTURE_DOCUMENTATION.txt"
    
    if Path(markdown_file).exists():
        convert_markdown_to_html(markdown_file, html_file)
        create_plain_text_version(markdown_file, text_file)
        
        print("\n" + "="*60)
        print("📋 INSTRUCTIONS FOR GOOGLE DOCS")
        print("="*60)
        print("1. Open the HTML file in your web browser")
        print("2. Select all content (Ctrl+A)")
        print("3. Copy (Ctrl+C)")
        print("4. Open Google Docs")
        print("5. Paste (Ctrl+V)")
        print("6. The formatting should be preserved")
        print("\nAlternative method:")
        print("1. Open the plain text file")
        print("2. Copy all content")
        print("3. Paste into Google Docs")
        print("4. Apply formatting manually")
        print("="*60)
    else:
        print(f"❌ Error: {markdown_file} not found!")
        print("Make sure you're running this script from the project root directory.")
