#!/usr/bin/env python3
"""
Standalone script to debug Recoll URL queries.
Takes a URL as a command-line argument and attempts to find it in the Recoll index.
"""

import os
import json
import argparse
from urllib.parse import unquote
from recoll import recoll

def get_document_content(db: recoll.connect, filename: str) -> dict:
    """Retrieve the full content of a document by its filename."""
    if db is None:
        return {"error": "Recoll database not available. Check configuration."}

    try:
        print(f"Attempting to query for filename: {filename}")

        query = db.query()
        # The query string needs to be properly quoted for Recoll
        nres = query.execute(f'filename:"{filename}"', fetchtext=True)

        if nres == 0:
            return {"error": f"Document with filename '{filename}' not found in index."}
        if nres > 1:
            return {"error": f"Multiple documents found for filename '{filename}'. Found {nres} results."}

        doc = query.fetchone()
        content = doc.text
        result_dict = {
            "status": "success",
            "input_filename": filename,
            "recoll_doc": {
                "filename": doc.filename,
                "url": doc.url,
                "mimetype": doc.mimetype,
            },
            "content_preview": content[:500] + ('...' if len(content) > 500 else ''),
        }
        return result_dict
    except Exception as e:
        return {"error": f"An exception occurred while processing filename '{filename}': {e}"}

def main():
    """Main function to parse arguments and run the query."""
    parser = argparse.ArgumentParser(description="Query Recoll for a document by its filename or dump filenames from the index.")
    parser.add_argument("filename", nargs='?', default=None, help="The filename of the document to search for.")
    parser.add_argument("--dump-filenames", type=int, nargs='?', const=10, default=None, help="Dump filenames from the index. Optionally specify a number of filenames to dump (default: 10).")
    args = parser.parse_args()

    # Set Recoll config directory
    os.environ['RECOLL_CONFDIR'] = os.path.expanduser('~/.recoll')

    # Initialize Recoll database connection
    try:
        db = recoll.connect()
    except Exception as e:
        print(f"Error: Could not connect to Recoll database: {e}", flush=True)
        return

    if args.dump_filenames is not None:
        print(f"Dumping first {args.dump_filenames} filenames from the index...")
        query = db.query()
        # An empty query is invalid. Use a query that matches all documents.
        nres = query.execute("filename:*")
        print(f"Found {nres} total documents.")
        for i in range(min(args.dump_filenames, nres)):
            doc = query.fetchone()
            print(f"  - \"{doc.filename}\"")
        return

    if args.filename:
        # Use the filename from the command-line arguments
        result = get_document_content(db, args.filename)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()