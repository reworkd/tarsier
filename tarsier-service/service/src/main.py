import uvicorn


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)


'''
curl -X POST http://localhost:8000/page-text \
-H "Content-Type: application/json" \
-H "Authorization: Bearer 21653deca0cc1ed46cbe73ef1cd6b8f542f8e8a2fbc23bd2ffeb2b22087e38467092c1736626aa25e20b3126df879ff3" \
-d '{
  "url": "https://hackernews.com"
}'


curl -X POST http://localhost:8000/extract \
-H "Content-Type: application/json" \
-d '{
  "url": "https://github.com/trending",
  "outputSchema": {
    "top_repo_title": {
        "type": "string",
        "description": "The title of the first repository on the page"
    },
    "top_repo_stars": {
        "type": "number",
        "description": "The number of stars that the top repo has"
    }
  },
  "options": {
    
  }
}'

curl -X POST http://localhost:8000/page-text \
-H "Authorization: Bearer 21653deca0cc1ed46cbe73ef1cd6b8f542f8e8a2fbc23bd2ffeb2b22087e38467092c1736626aa25e20b3126df879ff3" \


21653deca0cc1ed46cbe73ef1cd6b8f542f8e8a2fbc23bd2ffeb2b22087e38467092c1736626aa25e20b3126df879ff3
'''


