import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # User A
        await client.post('http://localhost:8000/auth/register', json={'username':'u1','email':'u1@a.com','display_name':'U1','password':'u1'})
        res_a = await client.post('http://localhost:8000/auth/login', data={'username':'u1','password':'u1'})
        token_a = res_a.json()['access_token']
        headers_a = {'Authorization': f'Bearer {token_a}'}
        user_a = (await client.get('http://localhost:8000/auth/me', headers=headers_a)).json()

        # User B
        await client.post('http://localhost:8000/auth/register', json={'username':'u2','email':'u2@b.com','display_name':'U2','password':'u2'})
        res_b = await client.post('http://localhost:8000/auth/login', data={'username':'u2','password':'u2'})
        token_b = res_b.json()['access_token']
        headers_b = {'Authorization': f'Bearer {token_b}'}
        user_b = (await client.get('http://localhost:8000/auth/me', headers=headers_b)).json()

        # A creates group
        res = await client.post('http://localhost:8000/groups', json={'name':'Group A','description':'test'}, headers=headers_a)
        group_id = res.json()['id']

        # A adds B to group
        await client.post(f'http://localhost:8000/groups/{group_id}/members', json={'user_id': user_b['id']}, headers=headers_a)

        # Get channels (A)
        res = await client.get(f'http://localhost:8000/groups/{group_id}/channels', headers=headers_a)
        channel_id = res.json()['channels'][0]['id']

        # A sends MSG 1
        await client.post(f'http://localhost:8000/channels/{channel_id}/messages', json={'content':'Msg from A'}, headers=headers_a)
        
        # B checks msgs
        res = await client.get(f'http://localhost:8000/channels/{channel_id}/messages', headers=headers_b)
        print("B sees:", [m['content'] for m in res.json()['messages']])

        # B replies
        await client.post(f'http://localhost:8000/channels/{channel_id}/messages', json={'content':'Reply from B'}, headers=headers_b)
        
        # A checks msgs
        res = await client.get(f'http://localhost:8000/channels/{channel_id}/messages', headers=headers_a)
        print("A sees:", [m['content'] for m in res.json()['messages']])

asyncio.run(main())
