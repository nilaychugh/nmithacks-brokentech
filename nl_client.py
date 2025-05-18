import sys
import asyncio
import aiohttp
import json

async def main():
    query = " ".join(sys.argv[1:])
    if not query:
        print("Please provide a natural language command")
        return
    
    try:
        # Use aiohttp to make HTTP request to the server
        async with aiohttp.ClientSession() as session:
            payload = {
                "jsonrpc": "2.0",
                "method": "process_natural_language",
                "params": {"query": query},
                "id": 1
            }
            
            async with session.post("http://localhost:8000/jsonrpc", 
                                     json=payload) as response:
                result = await response.json()
                if "result" in result:
                    print(result["result"])
                else:
                    print(f"Error: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())