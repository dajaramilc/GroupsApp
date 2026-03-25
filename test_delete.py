import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # User A
        res_a = await client.post('http://localhost:8000/auth/login', data={'username':'u1','password':'u1'})
        token_a = res_a.json().get('access_token')
        if not token_a:
            # register
            await client.post('http://localhost:8000/auth/register', json={'username':'u1','email':'u1@a.com','display_name':'U1','password':'u1'})
            token_a = (await client.post('http://localhost:8000/auth/login', data={'username':'u1','password':'u1'})).json()['access_token']
        headers_a = {'Authorization': f'Bearer {token_a}'}

        # User B
        res_b = await client.post('http://localhost:8000/auth/login', data={'username':'u2','password':'u2'})
        token_b = res_b.json().get('access_token')
        if not token_b:
            await client.post('http://localhost:8000/auth/register', json={'username':'u2','email':'u2@b.com','display_name':'U2','password':'u2'})
            token_b = (await client.post('http://localhost:8000/auth/login', data={'username':'u2','password':'u2'})).json()['access_token']
        headers_b = {'Authorization': f'Bearer {token_b}'}

        # User C
        res_c = await client.post('http://localhost:8000/auth/login', data={'username':'u3','password':'u3'})
        token_c = res_c.json().get('access_token')
        if not token_c:
            await client.post('http://localhost:8000/auth/register', json={'username':'u3','email':'u3@c.com','display_name':'U3','password':'u3'})
            token_c = (await client.post('http://localhost:8000/auth/login', data={'username':'u3','password':'u3'})).json()['access_token']
        headers_c = {'Authorization': f'Bearer {token_c}'}

        # A creates group
        res = await client.post('http://localhost:8000/groups', json={'name':'Delete me group','description':'test'}, headers=headers_a)
        group_id = res.json()['id']
        print(f"Group created: {group_id}")

        # A creates channel 2
        res = await client.post(f'http://localhost:8000/groups/{group_id}/channels', json={'name':'Todelete', 'description':''}, headers=headers_a)
        channel_id = res.json()['id']

        # B tries to delete channel (should fail! B is not even in group)
        fail_res = await client.delete(f'http://localhost:8000/channels/{channel_id}', headers=headers_b)
        print(f"B (non-member) delete channel: {fail_res.status_code}")

        # A adds B to group
        user_b_id = (await client.get('http://localhost:8000/auth/me', headers=headers_b)).json()['id']
        await client.post(f'http://localhost:8000/groups/{group_id}/members', json={'user_id': user_b_id}, headers=headers_a)

        # B tries to delete channel (should fail! B is member but NOT admin)
        fail_res = await client.delete(f'http://localhost:8000/channels/{channel_id}', headers=headers_b)
        print(f"B (member, non-admin) delete channel: {fail_res.status_code}")

        # A deletes channel (should succeed)
        res = await client.delete(f'http://localhost:8000/channels/{channel_id}', headers=headers_a)
        print(f"A deletes channel: {res.status_code}")

        # A removes B from group
        res = await client.delete(f'http://localhost:8000/groups/{group_id}/members/{user_b_id}', headers=headers_a)
        print(f"A removes B from group: {res.status_code}")

        # A deletes group
        res = await client.delete(f'http://localhost:8000/groups/{group_id}', headers=headers_a)
        print(f"A deletes group: {res.status_code}")

asyncio.run(main())
