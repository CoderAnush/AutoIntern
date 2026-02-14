#!/usr/bin/env python3
"""Debug resume upload"""
import httpx
import asyncio

async def test_resume_upload():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZjZmYTIxODUtNTY1Mi00M2ZhLWFlMWItMmY0MTNiYjlkNGNhIiwiZXhwIjoxNzcxMDg5NzM2LCJpYXQiOjE3NzEwODc5MzYsInR5cGUiOiJhY2Nlc3MifQ.tWeHAGuKXV27g1r9NC4UgHFVLDl59h2BWDhW_xJjEVs"

    with open(r"c:\Users\anush\Desktop\AutoIntern\AutoIntern\resume\test_resume.txt", 'rb') as f:
        files = {'file': ('test_resume.txt', f, 'text/plain')}
        headers = {'Authorization': f'Bearer {token}'}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8889/api/resumes/upload",
                    files=files,
                    headers=headers,
                    timeout=10
                )

                print(f"Status: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Exception: {type(e).__name__}: {e}")

asyncio.run(test_resume_upload())
