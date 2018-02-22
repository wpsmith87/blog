from flask import render_template, request, redirect, url_for

from . import app
from .database import session, Entry

PAGINATE_BY = 10

@app.route('/')
@app.route('/page/<int:page>')
def entries(page=1):
    """
    Query the database entries of the blog.
    :param page: The page number of the site.
    :return: Template page with the number of entries specified, Next/Previous links, page number, and total number of
    pages in the site
    
    """
    # Zero-indexed page
    default_entries = 10
    max_entries = 50

    # Set the number of entries displayed per page
    try:
        entry_limit = int(request.args.get('limit', default_entries))  # Get the limit from HTML argument 'limit'
        assert entry_limit > 0  # Ensure positive number
        assert entry_limit <= max_entries  # Ensure entries don't exceed max value
    except (ValueError, AssertionError):  # Use default value if number of entries doesn't meet expectations
        entry_limit = default_entries

    page_index = page - 1

    count = session.query(Entry).count()

    start = page_index * PAGINATE_BY  # Index of first entry on page
    end = start + PAGINATE_BY  # Index of last entry on page
    total_pages = (count - 1) // PAGINATE_BY + 1  # Total number of pages
    has_next = page_index < total_pages - 1  # Does following page exit?
    has_prev = page_index > 0  # Does previous page exist?

    entries = session.query(Entry)
    entries = entries.order_by(Entry.datetime.desc())
    entries = entries[start:end]

    return render_template('entries.html',
                           entries=entries,
                           has_next=has_next,
                           has_prev=has_prev,
                           page=page,
                           total_pages=total_pages
                           )
                           
    
@app.route('/entry/<int:id>')
def blog_entry(id):
    """
    Find a specific blog entry and display it.
    :param id: Entry ID value
    :return: Template page displaying the specified blog entry
    """
    entry = session.query(Entry).filter(Entry.id == id).one()  # Locate specific entry
    return render_template('blog_entry.html', entry=entry)  # Show the entry

@app.route('/entry/<int:id>/edit', methods=['GET'])
def edit_post_get(id):
    """
    Find a specific entry for editing.
    Uses the same functionality as general display utility.
    :param id: Entry ID value
    :return: Template page displaying the specified blog entry for modification
    """
    entry = session.query(Entry).filter(Entry.id == id).one()   # Locate specific entry
    return render_template('edit_post.html', entry=entry)  # Show the entry

@app.route('/entry/<int:id>/edit', methods=['POST'])
def edit_post_put(id, title=None, content=None):
    """
    Modify an existing blog entry.
    Having pulled the specific entry from the DB via GET call, uses POST call to update DB.
    :param id: Entry ID value
    :param title: Modified entry title
    :param content: Modified entry content
    :return: Default template page displaying all blog entries
    """
    entry = session.query(Entry).filter(Entry.id == id).one()  # Locate specific entry
    entry.title = request.form['title'],  # Update title
    entry.content = request.form["content"]  # Update entry content
    session.add(entry)  # Add modified entry to database
    session.commit()  # Update database
    return redirect(url_for('entries'))  # Return to entries page

@app.route('/entry/add', methods=['GET'])
def add_entry_get():
    return render_template('add_entry.html')
    

@app.route('/entry/add', methods=['POST'])
def add_entry_post():
    entry = Entry(
        title=request.form['title'],
        content=request.form['content'],
    )
    session.add(entry)
    session.commit()
    return redirect(url_for('entries'))
    
@app.route('/entry/<int:id>/delete_it') 
def delete_entry_page(id):
    entry = session.query(Entry).filter(Entry.id == id).one()  # Locate specific entry
    return render_template('delete_entry.html', entry=entry)

@app.route('/entry/<int:id>/delete')
def delete_entry(id):
    """Delete an existing entry"""
    entry = session.query(Entry).filter(Entry.id == id).one()  # Locate specific entry
    session.delete(entry)  # Delete specified entry
    session.commit()  # Update database
    return redirect(url_for('entries'))  # Return to entries page