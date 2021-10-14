# psts-api-front-end
A website that serves as a front end for a blog API.  
Check it out here at [fastapi.psts.xyz/](https://fastapi.psts.xyz/).
The backend is here at [api.psts.xyz](https://api.psts.xyz/).

## Description
The purpose of this site is to be a user interface to interact with the backend for data. 
It has pages for users to register and log in with. There are pages to view all recent posts, posts from all other user's that the current user has followed and pages to view specific user's posts.
There are forms for creating and editing posts and replies.
I deployed this app myself on a Linode server remotely through ssh using nginx and uvicorn.

## Learned on project
- got a familiarity to FastAPI web framework (was very similar coming from Flask)
- learned to make back end and front end and connect the two  
  - Learned my original endpoints on my API were not enough
  - Original API had simple single post, reply queries
  - The view all posts required 1 query for the post and then 5+ requests for each reply
  - I made more efficient API endpoints which gathered more data all in 1 request

## Tech
- Python
- FastAPI web framework
- Bootstrap/CSS for styling
- Jinja2 html templates
- Nginx and Uvicorn hosted on my Linode Ubuntu server
