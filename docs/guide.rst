Developer guide
===============

Architecture
------------

* ``main.py`` mounts API routers under ``/api`` and configures middleware.
* ``src/routes`` validates requests and applies authentication dependencies.
* ``src/repository`` queries and commits database records. Ownership checks live
  in the relevant queries; callers must not bypass them.
* ``src/services`` handles JWTs, email, Cloudinary, QR generation and rate limits.
* ``src/entity`` defines SQLAlchemy tables and relationships.
* ``src/schemas`` defines Pydantic input and output contracts.
* ``src/database/db.py`` yields sessions, rolls back exceptions and closes sessions.

Run the application
-------------------

Use the project virtual environment and install the dependencies listed in
``requirements.txt``. Supply configuration privately using the existing settings
in ``src/conf/config.py``; never publish real credentials in documentation.
Start PostgreSQL and Redis, configure Cloudinary and email, and then run:

.. code-block:: console

   venv/bin/alembic upgrade head
   venv/bin/uvicorn main:app --reload

Review migrations before applying them to populated databases. In particular,
adding a non-null owner column to existing photos requires assigning real owners.
Swagger is available at ``/docs`` for exploring and testing API endpoints.

Authentication and permissions
------------------------------

Register through ``POST /api/auth/signup``, confirm the email and log in through
``POST /api/auth/login``. Login uses the email in the OAuth2 ``username`` field.
Send the access token using ``Authorization: Bearer <access_token>``.

The first registration into an empty users table becomes ``admin``; subsequent
registrations become ``user``. The registration repository uses a PostgreSQL
transaction advisory lock to serialize that decision.

* Photo owners and administrators can read, update and delete accessible photos.
* Owners and administrators can create transformations and QR codes.
* Authenticated users can comment on other users' photos.
* Only a comment's author can edit it, including when the caller is an administrator.
* Administrators and moderators can delete comments; ordinary users cannot.
* ``PATCH /api/users/role`` changes a role by email and requires administrator
  rights checked against the database. It invalidates the target's Redis cache.
* ``GET /api/users/admin`` and ``GET /api/users/moderator`` only check access;
  they do not assign roles.

Photo and QR workflow
---------------------

1. ``POST /api/photos/upload`` accepts multipart ``file``, required ``description``
   and optional tag names. Repeated tag fields and comma-separated entries are
   supported. At most five input names are accepted; names are stripped,
   lowercased and deduplicated. Tags are globally shared.
2. ``GET /api/photos`` lists photos with pagination. The optional search matches
   the image URL. ``GET /api/photos/{photo_id}`` redirects an authorized caller
   to the original image or a requested transformed URL.
3. ``PUT /api/photos/{photo_id}`` updates supplied description and tags. Omitting
   a field preserves it; an empty tag list removes associations, not global tags.
4. ``POST /api/photos/transform?photo_id=15&transformation=avatar`` persists a
   transformation and returns its ID and public ``image_url``. Available presets
   are ``avatar`` (round 200x200 face thumbnail), ``resize`` (fit within 800x800)
   and ``grayscale``. The original asset is unchanged.
5. ``POST /api/photos/qrcode?transformation_id=7`` takes the saved transformation
   ID, not the original photo ID. It creates a QR PNG in Cloudinary and stores
   ``qr_code_url``. Repeated calls return the existing QR when present.
6. Open the QR image on another screen and scan it. The encoded URL points directly
   to Cloudinary, so viewing the result requires internet access but no JWT or
   connection to the developer's local server.

The shared ``upload_stream`` service runs Cloudinary uploads in a worker thread.
QR generation also runs in a worker thread and keeps its in-memory buffer open
until upload completes. URLs are persisted in ``photo_transformations``.

Comments
--------

The current router prefix produces these paths:

.. code-block:: text

   POST   /api/comments/photos/{photo_id}/comments
   GET    /api/comments/photos/{photo_id}/comments
   PUT    /api/comments/comments/{comment_id}
   DELETE /api/comments/comments/{comment_id}

Creation and editing accept JSON such as ``{"text": "Beautiful photo!"}``.
Comments are linked to one photo; a photo can have many comments. The database
sets ``created_at`` and ``updated_at`` on insertion. SQLAlchemy includes an
``updated_at`` update when the mapped record changes. This is not a database
trigger for arbitrary external SQL updates. Legacy comments with unknown authors
cannot be edited through the author-only query.

The backend provides the list API; rendering a comment block under a photo is a
frontend responsibility.

Operational limits
------------------

Cloudinary files and PostgreSQL records do not share a transaction: an upload
can remain if the following database commit fails. Deleting photo metadata does
not currently delete its Cloudinary assets. Concurrent creation of the same new
tag can raise a unique-constraint error. Public Cloudinary links are not revoked
by removing a database record. Access tokens remain valid until expiration after
a password reset; resetting the password clears the stored refresh token.

Build documentation
-------------------

Sphinx 9.1.0 was used to verify this documentation. From the project root:

.. code-block:: console

   venv/bin/python -m sphinx -W --keep-going -b html docs docs/_build/html

Open ``docs/_build/html/index.html``. The local Sphinx extension reads Python
syntax and docstrings without importing the application. No database, Redis,
SMTP connection or secret environment configuration is required for this build.
Generated reference pages refresh automatically on each build.
