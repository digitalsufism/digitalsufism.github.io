#!/usr/bin/env python3
"""
Bibliography Extraction Script for Digital Sufism Project
Converts primary_recent.html to structured JSON database
"""

from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

def extract_general_footnotes(soup):
    """Extract general footnotes (IDs: one through five)"""
    general_footnotes = []
    endnotes_section = soup.find('section', id='end-notes')
    if not endnotes_section:
        return general_footnotes

    general_ids = ['one', 'two', 'three', 'four', 'five']
    footnote_list = endnotes_section.find('ol')

    if footnote_list:
        # Don't use recursive=False because HTML is malformed
        for li in footnote_list.find_all('li'):
            footnote_id = li.get('id')
            if footnote_id in general_ids:
                # Get text content, removing the back arrow link
                text = li.get_text(separator=' ', strip=True)
                # Remove the ↵ back arrow at the end
                text = re.sub(r'↵\s*$', '', text)

                # Extract backlink target
                backlink = li.find('a', href=True)
                backlink_target = backlink['href'].replace('#', '') if backlink else None

                general_footnotes.append({
                    'id': footnote_id,
                    'text': text,
                    'backlinkTarget': backlink_target
                })

    return general_footnotes

def extract_work_specific_footnotes(soup):
    """Extract work-specific footnotes (IDs: six through fourteen)"""
    work_footnotes = []
    endnotes_section = soup.find('section', id='end-notes')
    if not endnotes_section:
        print("   ⚠ Warning: Could not find end-notes section")
        return work_footnotes

    work_ids = ['six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen']
    footnote_list = endnotes_section.find('ol')

    if not footnote_list:
        print("   ⚠ Warning: Could not find <ol> in end-notes section")
        return work_footnotes

    # Don't use recursive=False because HTML is malformed (li #6 unclosed, nesting others)
    all_lis = footnote_list.find_all('li')
    print(f"   Found {len(all_lis)} total footnote <li> elements")

    if footnote_list:
        for li in footnote_list.find_all('li'):
            footnote_id = li.get('id')
            if footnote_id in work_ids:
                print(f"   Found work-specific footnote: {footnote_id}")
                # Get text content
                text = li.get_text(separator=' ', strip=True)
                text = re.sub(r'↵\s*$', '', text)

                # Extract backlink target (work ID)
                backlink = li.find('a', href=True)
                backlink_target = backlink['href'].replace('#', '') if backlink else None

                work_footnotes.append({
                    'id': footnote_id,
                    'text': text,
                    'backlinkTarget': backlink_target,
                    'relatedWorkIds': []  # Will be populated during work extraction
                })
            else:
                if footnote_id:
                    print(f"   Skipping footnote with id: {footnote_id}")

    return work_footnotes

def extract_author_name_and_death(author_link):
    """Extract author name and death information from button text"""
    text = author_link.get_text(strip=True)

    # Check for multiple works indicator (+) first
    has_multiple = '(+)' in text

    # Pattern 1: "Name (d. Location, Date)" or "Name (ex. Location, Date)"
    match = re.search(r'(.+?)\s*\((d\.|ex\.)\s*(.+?),\s*(.+?)\)', text)
    if match:
        name = match.group(1).strip()
        location = match.group(3).strip()
        death_date = match.group(4).strip()
        name = name.replace('(+)', '').strip()

        return {
            'name': name,
            'deathLocation': location,
            'deathDate': death_date,
            'hasMultipleWorks': has_multiple
        }

    # Pattern 2: "Name (d. fl. ca. Date)" - flourished date, no location
    match = re.search(r'(.+?)\s*\(d\.\s*fl\.\s*ca\.\s*(.+?)\)', text)
    if match:
        name = match.group(1).strip()
        death_date = match.group(2).strip()
        name = name.replace('(+)', '').strip()

        return {
            'name': name,
            'deathLocation': '',
            'deathDate': 'fl. ca. ' + death_date,
            'hasMultipleWorks': has_multiple
        }

    # Pattern 3: "Name (+) (d. Date)" - no location
    match = re.search(r'(.+?)\s*\(d\.\s*(.+?)\)', text)
    if match:
        name = match.group(1).strip()
        death_date = match.group(2).strip()
        name = name.replace('(+)', '').strip()

        return {
            'name': name,
            'deathLocation': '',
            'deathDate': death_date,
            'hasMultipleWorks': has_multiple
        }

    # Pattern 4: Anonymous or unusual format - extract what we can
    if 'Anonymous' in text or ',' in text:
        name = text.replace('(+)', '').strip()
        return {
            'name': name,
            'deathLocation': '',
            'deathDate': '',
            'hasMultipleWorks': has_multiple
        }

    return None

def determine_work_type(button_classes):
    """Determine work type based on button class"""
    if 'btn-info' in button_classes:
        return 'isnad'
    elif 'btn-warning' in button_classes:
        return 'reconstruction'
    elif 'btn-danger' in button_classes:
        return 'uncertain'
    else:
        return 'discursive'

def extract_citations(citation_div, citation_type):
    """Extract editions, translations, manuscripts, or reproductions"""
    citations = []

    if not citation_div:
        return citations

    ol = citation_div.find('ol')
    if not ol:
        return citations

    for li in ol.find_all('li', recursive=False):
        # Get citation text
        citation_text = ''
        for content in li.contents:
            if isinstance(content, str):
                citation_text += content
            elif content.name != 'a':
                citation_text += content.get_text()

        citation_text = citation_text.strip()

        # Check for partial marker
        is_partial = citation_text.startswith('Partial:')
        if is_partial:
            citation_text = citation_text.replace('Partial:', '').strip()

        # Extract link if present
        link_tag = li.find('a', href=True)
        link = link_tag['href'] if link_tag else ''

        # Extract language for translations (pattern: [Language])
        language = ''
        if citation_type == 'translations':
            lang_match = re.search(r'\[([^\]]+)\]', citation_text)
            if lang_match:
                language = lang_match.group(1)

        citation_obj = {
            'citation': citation_text,
            'link': link,
            'type': 'partial' if is_partial else 'complete'
        }

        if citation_type == 'translations':
            citation_obj['language'] = language

        citations.append(citation_obj)

    return citations

def extract_work(work_div, work_button, author_id):
    """Extract a single work's complete bibliographic data"""
    work_id = work_div.get('id', '')
    title_elem = work_button
    title = title_elem.get_text(strip=True)

    work_type = determine_work_type(work_button.get('class', []))

    # The work_div IS the collapse div containing all work data
    content = work_div
    if not content:
        return None

    work_data = {
        'id': work_id if work_id else f"{author_id}-work",
        'title': title,
        'titleVariants': [],
        'titleTranslation': '',
        'type': work_type,
        'scholarlyCommentary': '',
        'editions': [],
        'translations': [],
        'manuscripts': [],
        'reproductions': []
    }

    # Extract editions
    editions_div = content.find('div', id=lambda x: x and '-ed' in x)
    if editions_div:
        work_data['editions'] = extract_citations(editions_div, 'editions')

    # Extract translations
    translations_div = content.find('div', id=lambda x: x and '-tr' in x)
    if translations_div:
        work_data['translations'] = extract_citations(translations_div, 'translations')

    # Extract manuscripts
    manuscripts_div = content.find('div', id=lambda x: x and '-ms' in x)
    if manuscripts_div:
        work_data['manuscripts'] = extract_citations(manuscripts_div, 'manuscripts')

    # Extract reproductions
    reproductions_div = content.find('div', id=lambda x: x and '-repr' in x)
    if reproductions_div:
        work_data['reproductions'] = extract_citations(reproductions_div, 'reproductions')

    # Extract footnote references (for scholarly commentary)
    footnote_refs = work_button.find_all('sup')
    footnote_ids = []
    for sup in footnote_refs:
        link = sup.find('a', href=True)
        if link:
            footnote_id = link['href'].replace('#', '')
            footnote_ids.append(footnote_id)

    work_data['footnoteRefs'] = footnote_ids

    return work_data

def extract_author_direct(author_link, author_content, century):
    """Extract a single author and all their works from link and content div"""
    author_info = extract_author_name_and_death(author_link)
    if not author_info:
        return None

    # Generate author ID from name
    name_parts = author_info['name'].split()
    author_id = '-'.join(name_parts[-2:]).lower() if len(name_parts) >= 2 else name_parts[-1].lower()
    author_id = re.sub(r'[^a-z-]', '', author_id)

    author_data = {
        'id': author_id,
        'name': author_info['name'],
        'nameArabic': '',
        'deathDate': author_info['deathDate'],
        'deathLocation': author_info['deathLocation'],
        'century': century,
        'hasMultipleWorks': author_info['hasMultipleWorks'],
        'authorNote': '',
        'works': []
    }

    # Check for author-level note (like Muhasibi's bibliography note)
    note_p = author_content.find('p')
    if note_p:
        author_data['authorNote'] = note_p.get_text(strip=True)

    # Extract all works - find buttons with btn class AND a type class
    work_buttons = []
    all_buttons = author_content.find_all('button')
    for button in all_buttons:
        button_classes = button.get('class', [])
        # Check if button has 'btn' class and one of the type classes
        if 'btn' in button_classes and any(cls in button_classes for cls in ['btn-light', 'btn-info', 'btn-warning', 'btn-danger']):
            # Make sure it's not the author button (which has btn-default)
            if 'btn-default' not in button_classes and 'btn-link' not in button_classes:
                work_buttons.append(button)

    # Debug: print button counts for this author
    if len(work_buttons) > 0:
        print(f"      {author_data['name']}: found {len(work_buttons)} work buttons")

    for work_button in work_buttons:
        # Find the corresponding collapse div
        target_id = work_button.get('data-target', '').replace('#', '')
        if not target_id:
            print(f"         ⚠ Warning: Work button has no data-target: {work_button.get_text(strip=True)[:50]}")
            continue

        work_div = author_content.find('div', id=target_id)
        if work_div:
            work_data = extract_work(work_div, work_button, author_id)
            if work_data:
                author_data['works'].append(work_data)
        else:
            print(f"         ⚠ Warning: Could not find work div with id='{target_id}'")

    return author_data

def extract_century(century_section):
    """Extract all authors from a century section"""
    authors = []

    # Get century label
    century_button = century_section.find('button', class_='btn-link')
    if not century_button:
        return authors, ''

    century_text = century_button.get_text(strip=True)
    century_match = re.search(r'(\d+[a-z]{2}/\d+[a-z]{2})\s+Century', century_text)
    century = century_match.group(1) if century_match else ''

    # Find the collapse div containing all authors
    century_content = century_section.find('div', class_='collapse')
    if not century_content:
        return authors, century

    # Find all author links directly (marked by btn btn-default with user-edit icon)
    author_links = []
    for elem in century_content.find_all('a', class_='btn-default'):
        # Check if this is an author link (has user-edit icon)
        if elem.find('i', class_='fa-user-edit'):
            author_links.append(elem)

    print(f"      Found {len(author_links)} author links in {century} century")

    # For each author link, find its corresponding collapse div
    for author_link in author_links:
        # Get the href to find the author's content div
        author_id = author_link.get('href', '').replace('#', '')
        if not author_id:
            continue

        # Find the collapse div with this ID
        author_content_div = century_content.find('div', id=author_id)
        if not author_content_div:
            print(f"         ⚠ Warning: Could not find author content div with id='{author_id}'")
            continue

        # Pass both the link and content div to extract_author
        author_data = extract_author_direct(author_link, author_content_div, century)
        if author_data:
            authors.append(author_data)
        else:
            author_text = author_link.get_text(strip=True)[:60]
            print(f"         ⚠ Warning: Failed to extract author: {author_text}")

    return authors, century

def main():
    print("📚 Digital Sufism Bibliography Extraction Script")
    print("=" * 60)

    # Load HTML file
    print("\n1️⃣  Loading primary_recent.html...")
    with open('primary_recent.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    print("✓ HTML loaded successfully")

    # Extract general footnotes
    print("\n2️⃣  Extracting general footnotes (1-5)...")
    general_footnotes = extract_general_footnotes(soup)
    print(f"✓ Extracted {len(general_footnotes)} general footnotes")

    # Extract work-specific footnotes
    print("\n3️⃣  Extracting work-specific footnotes (6-14)...")
    work_footnotes = extract_work_specific_footnotes(soup)
    print(f"✓ Extracted {len(work_footnotes)} work-specific footnotes")

    # Extract all authors and works
    print("\n4️⃣  Extracting bibliography by century...")
    all_authors = []

    # Find all century sections
    bibliography_section = soup.find('section', id='feature-one')
    if bibliography_section:
        century_cards = bibliography_section.find_all('div', class_='card')

        for card in century_cards:
            authors, century = extract_century(card)
            print(f"   - {century}: {len(authors)} authors")
            all_authors.extend(authors)

    # Calculate totals
    total_authors = len(all_authors)
    total_works = sum(len(author['works']) for author in all_authors)

    print(f"\n✓ Extracted {total_authors} authors")
    print(f"✓ Extracted {total_works} works")

    # Build final JSON structure
    print("\n5️⃣  Building JSON structure...")
    bibliography_data = {
        'metadata': {
            'totalAuthors': total_authors,
            'totalWorks': total_works,
            'lastUpdated': datetime.now().isoformat(),
            'version': '1.0',
            'extractedFrom': 'primary_recent.html',
            'generalFootnotes': general_footnotes
        },
        'authors': all_authors,
        'workSpecificFootnotes': work_footnotes
    }

    # Link footnotes to works using backlink targets
    print("\n6️⃣  Linking footnotes to works using backlink targets...")

    # Build map of work ID to work object
    work_map = {}
    for author in all_authors:
        for work in author['works']:
            work_map[work['id']] = work

    # Link each footnote to its work using the backlink target
    linked_count = 0
    for footnote in work_footnotes:
        backlink_target = footnote.get('backlinkTarget')
        if backlink_target and backlink_target in work_map:
            work = work_map[backlink_target]

            # Add commentary to work
            if work['scholarlyCommentary']:
                work['scholarlyCommentary'] += ' '
            work['scholarlyCommentary'] += footnote['text']

            # Record relationship
            footnote['relatedWorkIds'].append(work['id'])
            linked_count += 1
        else:
            if backlink_target:
                print(f"   ⚠ Warning: Footnote '{footnote['id']}' references unknown work '{backlink_target}'")
            else:
                print(f"   ⚠ Warning: Footnote '{footnote['id']}' has no backlink target")

    # Clean up temporary footnoteRefs field from works
    for author in all_authors:
        for work in author['works']:
            if 'footnoteRefs' in work:
                del work['footnoteRefs']

    print(f"✓ Linked {linked_count} footnotes to works")

    # Save to JSON
    print("\n7️⃣  Saving to data/bibliography.json...")
    with open('data/bibliography.json', 'w', encoding='utf-8') as f:
        json.dump(bibliography_data, f, ensure_ascii=False, indent=2)

    print("✓ Saved successfully")

    # Summary
    print("\n" + "=" * 60)
    print("📊 EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total Authors:           {total_authors}")
    print(f"Total Works:             {total_works}")
    print(f"General Footnotes:       {len(general_footnotes)}")
    print(f"Work-specific Footnotes: {len(work_footnotes)}")
    print(f"\nOutput: data/bibliography.json")
    print("=" * 60)
    print("\n✅ Extraction complete!")

if __name__ == '__main__':
    main()
