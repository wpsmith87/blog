from flask import render_template, request, redirect, url_for, flash

from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import Forbidden

from .database import User, Entry, session
from . import app



PAGINATE_BY = 10

@app.route("/")
@app.route("/page/<int:page>")
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
        entry_limit = int(request.args.get("limit", default_entries))  # Get the limit from HTML argument 'limit'
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

    return render_template("entries.html",
                           entries=entries,
                           has_next=has_next,
                           has_prev=has_prev,
                           page=page,
                           total_pages=total_pages
                           )
                           

#
#  View Single Entry  #
#
    
@app.route("/entry/<int:id>")
def blog_entry(id):
    """
    Find a specific blog entry and display it.
    :param id: Entry ID value
    :return: Template page displaying the specified blog entry
    """
    entry = session.query(Entry).filter(Entry.id == id).one()  # Locate specific entry
    return render_template("blog_entry.html", entry=entry)  # Show the entry

#
#  Edit Entry  #
#

@app.route("/entry/<int:id>/edit", methods=['GET'])
@login_required  # Force authentication
def edit_post_get(id):
    """
    Find a specific entry for editing.
    Uses the same functionality as general display utility.
    :param id: Entry ID value
    :return: Template page displaying the specified blog entry for modification
    """
    entry = session.query(Entry).filter(Entry.id == id).one()   # Locate specific entry
    if not all([entry.author, current_user]) or entry.author.id != current_user.id:
        flash("Only the author can edit.", "danger")
        return redirect(url_for("entries"))
        
    return render_template("edit_post.html", entry=entry) # Edit entry

@app.route("/entry/<int:id>/edit", methods=['POST'])
@login_required  # Force authentication
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
    
    if not all([entry.author, current_user]) or entry.author.id != current_user.id:
        flash('Only the author can edit.')
        return render_template("blog_entry.html", entry=entry) # Show the entry
        
    entry.title = request.form['title'],  # Update title
    entry.content = request.form["content"]  # Update entry content
    session.add(entry)  # Add modified entry to database
    session.commit()  # Update database
    return redirect(url_for('entries'))  # Return to entries page

#
#  Add Entry  #
#

@app.route("/entry/add", methods=["GET"])
@login_required  # Force authentication
def add_entry_get():
    return render_template("add_entry.html")

@app.route("/entry/add", methods=["POST"])
@login_required  # Force authentication
def add_entry_post():
    entry = Entry(
        title=request.form["title"],
        content=request.form["content"],
        author=current_user
    )
    session.add(entry)
    session.commit()
    return redirect(url_for("entries"))
    
#
#  Delete Entry  #
#    
    
@app.route("/entry/<int:id>/delete_it") 
@login_required  # Force authentication
def delete_entry_page(id):
    entry = session.query(Entry).filter(Entry.id == id).one()  # Locate specific entry
    
    if not all([entry.author, current_user]) or entry.author.id != current_user.id:
        flash("Only the author can delete.", "danger")
        return redirect( url_for("entries")) # Show the entry
    
    return render_template("delete_entry.html", entry=entry)

@app.route("/entry/<int:id>/delete")
@login_required  # Force authentication
def delete_entry(id):
    """Delete an existing entry"""
    entry = session.query(Entry).filter(Entry.id == id).one()  # Locate specific entry
    
    if not all([entry.author, current_user]) or entry.author.id != current_user.id:
        flash("Only the author can delete.", "danger")
        return redirect( url_for("entries")) # Show the entry
    
    session.delete(entry)  # Delete specified entry
    session.commit()  # Update database
    return redirect(url_for("entries"))  # Return to entries page
    
#
#  User signup  #
#


@app.route("/signup", methods=["GET"])
def signup_get():
    return render_template("signup.html")
   
@app.route("/signup", methods=["POST"])
def signup_post():
    
    name=request.form["name"]
    email=request.form["email"]
    password=request.form["password"]
    password_2=request.form["repassword"]
    
    if session.query(User).filter_by(email=email).first():
        flash("User with that email address already exists", "danger")
        return redirect(url_for("signup_get"))
    
    if len(password and password_2) < 8 or password != password_2:
        flash("Passwords did not match", "danger")
        return redirect(url_for("signup_get"))
    
    user = User(name=name, 
    email=email, 
    password=generate_password_hash(password))
                
    session.add(user)
    session.commit()
    login_user(user)
    
    flash("You are now a user!", "info")
    return redirect(request.args.get('next') or url_for("entries"))
    
    
#
#  User Login  #
#    
    
    
@app.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    email = request.form["email"]
    password = request.form["password"]
    user = session.query(User).filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        flash("Incorrect username or password", "danger")
        return redirect(url_for("login_get"))

    login_user(user)
    return redirect(request.args.get('next') or url_for("entries"))
    
#
#  Logout  #
#     

@app.route("/logout")
@login_required  # Force authentication
def logout():
    """Log user out of system"""
    logout_user()
    flash("You have been logged out", "danger")
    return redirect(url_for("login_get"))