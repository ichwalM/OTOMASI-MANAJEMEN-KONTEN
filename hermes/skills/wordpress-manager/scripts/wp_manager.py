#!/usr/bin/env python3
"""
WordPress REST API CLI Manager for Hermes Agent.
Uses Python standard library (no external dependencies required).
"""

import os
import sys
import json
import base64
import argparse
from urllib import request, parse, error

def get_auth_header(user, app_password):
    credentials = f"{user}:{app_password}".strip()
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return f"Basic {encoded}"

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data is not None:
        req_data = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            if res_body:
                try:
                    return json.loads(res_body)
                except json.JSONDecodeError:
                    return {"raw": res_body}
            return {"status": "success", "code": response.status}
    except error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("message", error_body)
        except Exception:
            msg = error_body
        sys.stderr.write(f"HTTP Error {e.code}: {msg}\n")
        sys.exit(1)
    except error.URLError as e:
        sys.stderr.write(f"Connection Error: {e.reason}\n")
        sys.exit(1)

def get_base_url():
    base_url = os.environ.get("WORDPRESS_URL", "http://wordpress").rstrip("/")
    # If base url does not have /wp-json
    return f"{base_url}/wp-json/wp/v2"

def main():
    parser = argparse.ArgumentParser(description="WordPress REST API Manager for Hermes Agent")
    parser.add_argument("--url", help="WordPress URL (defaults to env WORDPRESS_URL or http://wordpress)")
    parser.add_argument("--user", help="WordPress User (defaults to env WORDPRESS_USER or admin)")
    parser.add_argument("--password", help="WordPress Application Password (defaults to env WORDPRESS_APP_PASSWORD)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-posts
    list_p = subparsers.add_parser("list-posts", help="List recent WordPress posts")
    list_p.add_argument("--limit", type=int, default=10, help="Number of posts to return")
    list_p.add_argument("--status", default="any", help="Status filter: any, publish, draft, trash")

    # get-post
    get_p = subparsers.add_parser("get-post", help="Get a single post by ID")
    get_p.add_argument("--id", type=int, required=True, help="Post ID")

    # create-post
    create_p = subparsers.add_parser("create-post", help="Create a new WordPress post")
    create_p.add_argument("--title", required=True, help="Post title")
    create_p.add_argument("--content", required=True, help="Post content (HTML supported)")
    create_p.add_argument("--status", default="publish", choices=["publish", "draft", "private"], help="Post status")
    create_p.add_argument("--categories", help="Comma-separated category IDs")

    # update-post
    update_p = subparsers.add_parser("update-post", help="Update an existing post")
    update_p.add_argument("--id", type=int, required=True, help="Post ID to update")
    update_p.add_argument("--title", help="New post title")
    update_p.add_argument("--content", help="New post content (HTML supported)")
    update_p.add_argument("--status", choices=["publish", "draft", "private", "trash"], help="New post status")

    # delete-post
    del_p = subparsers.add_parser("delete-post", help="Delete a post")
    del_p.add_argument("--id", type=int, required=True, help="Post ID to delete")
    del_p.add_argument("--force", action="store_true", help="Bypass trash and permanently delete")

    args = parser.parse_args()

    wp_url = (args.url or os.environ.get("WORDPRESS_URL", "http://wordpress")).rstrip("/")
    wp_user = args.user or os.environ.get("WORDPRESS_USER", "admin")
    wp_pass = args.password or os.environ.get("WORDPRESS_APP_PASSWORD", "")

    api_base = f"{wp_url}/wp-json/wp/v2"
    headers = {
        "User-Agent": "Hermes-WordPress-Manager/1.0"
    }

    if wp_pass:
        headers["Authorization"] = get_auth_header(wp_user, wp_pass)

    if args.command == "list-posts":
        query_params = {"per_page": args.limit}
        if args.status != "any":
            query_params["status"] = args.status
        url = f"{api_base}/posts?{parse.urlencode(query_params)}"
        res = make_request(url, headers=headers)
        
        output = []
        for post in res:
            output.append({
                "id": post.get("id"),
                "title": post.get("title", {}).get("rendered", ""),
                "status": post.get("status"),
                "date": post.get("date"),
                "link": post.get("link")
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))

    elif args.command == "get-post":
        url = f"{api_base}/posts/{args.id}"
        post = make_request(url, headers=headers)
        output = {
            "id": post.get("id"),
            "title": post.get("title", {}).get("rendered", ""),
            "status": post.get("status"),
            "date": post.get("date"),
            "link": post.get("link"),
            "content": post.get("content", {}).get("rendered", "")
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))

    elif args.command == "create-post":
        url = f"{api_base}/posts"
        payload = {
            "title": args.title,
            "content": args.content,
            "status": args.status
        }
        if args.categories:
            cat_ids = [int(c.strip()) for c in args.categories.split(",") if c.strip().isdigit()]
            if cat_ids:
                payload["categories"] = cat_ids
        
        post = make_request(url, method="POST", data=payload, headers=headers)
        print(json.dumps({
            "success": True,
            "action": "created",
            "id": post.get("id"),
            "title": post.get("title", {}).get("rendered", ""),
            "status": post.get("status"),
            "link": post.get("link")
        }, indent=2, ensure_ascii=False))

    elif args.command == "update-post":
        url = f"{api_base}/posts/{args.id}"
        payload = {}
        if args.title is not None:
            payload["title"] = args.title
        if args.content is not None:
            payload["content"] = args.content
        if args.status is not None:
            payload["status"] = args.status

        if not payload:
            sys.stderr.write("Error: No updates specified. Provide --title, --content, or --status.\n")
            sys.exit(1)

        post = make_request(url, method="POST", data=payload, headers=headers)
        print(json.dumps({
            "success": True,
            "action": "updated",
            "id": post.get("id"),
            "title": post.get("title", {}).get("rendered", ""),
            "status": post.get("status"),
            "link": post.get("link")
        }, indent=2, ensure_ascii=False))

    elif args.command == "delete-post":
        query_params = {"force": "true" if args.force else "false"}
        url = f"{api_base}/posts/{args.id}?{parse.urlencode(query_params)}"
        res = make_request(url, method="DELETE", headers=headers)
        print(json.dumps({
            "success": True,
            "action": "deleted",
            "id": args.id,
            "status": res.get("status")
        }, indent=2))

if __name__ == "__main__":
    main()
