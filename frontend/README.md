# PhotoShare frontend

The frontend uses plain HTML, CSS and JavaScript. No Node packages or build step are required.

Start the configured backend from the project root:

```bash
venv/bin/uvicorn main:app --reload
```

Open **http://localhost:8000/app/**. Requests use the same origin and the existing `/api` endpoints.
PostgreSQL, Redis, Cloudinary and mail settings must be configured and database migrations applied.

Register, confirm your email, then sign in. Email confirmation and password reset pages accept the token from the email link. JWTs are stored in sessionStorage for the browser tab and removed on sign-out. Expired access tokens are refreshed automatically.

You can browse photos, upload with up to five tags, edit/delete your photos, comment, generate transformations and public QR links, and change roles as an administrator. Administrators can also manage other users' photos; moderators can delete comments. The backend remains authoritative for permissions.

The gallery filters loaded photos locally by description and tags. Use **Load more photos** for further pages, including on My Photos. The backend has no user-list endpoint, so administration uses email lookup rather than a simulated user table. Likes and custom transformation sizes are not offered because the API does not implement them.

The interface contains no demo accounts or sample photos. An empty database shows an empty gallery.
