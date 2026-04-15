import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Register user a
        await client.post('http://localhost:8000/auth/register', json={'username':'a1','email':'a1@a.com','display_name':'a1','password':'a1'})
        # Login user a
        res = await client.post('http://localhost:8000/auth/login', data={'username':'a1','password':'a1'})
        token_a = res.json().get('access_token')
        if not token_a: print("Login failed:", res.json()); return
        headers_a = {'Authorization': f'Bearer {token_a}'}

        # Create group
        res = await client.post('http://localhost:8000/groups', json={'name':'g1','description':'g1'}, headers=headers_a)
        group_id = res.json().get('id', None)
        if not group_id: print("Failed group block:", res.json()); return

        # Get channels
        res = await client.get(f'http://localhost:8000/groups/{group_id}/channels', headers=headers_a)
        channel_id = res.json()['channels'][0]['id']

        # Send channel msg
        res = await client.post(f'http://localhost:8000/channels/{channel_id}/messages', json={'content':'hello channel'}, headers=headers_a)
        print('Send msg status:', res.status_code, res.text)

        # Get channel msgs
        res = await client.get(f'http://localhost:8000/channels/{channel_id}/messages', headers=headers_a)
        print('Get msgs status:', res.status_code, res.text)

asyncio.run(main())
