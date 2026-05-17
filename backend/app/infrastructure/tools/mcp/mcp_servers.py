import json
import asyncio
from config.settings import settings
from agents.mcp import MCPServerSse, MCPServerStreamableHttp
from typing import Dict, Any

search_mac_client_streamable = MCPServerStreamableHttp(
    name="通用联网搜索-StreamableHTTP",
    params={
        "url": f"{settings.DASHSCOPE_BASE_URL}",
        "headers": {
            "Authorization": f"Bearer {settings.AL_BAILIAN_API_KEY}",
        },
        "timeout": 60,
        "sse_read_timeout": 60 * 30,
    },
    client_session_timeout_seconds=60 * 10,
    cache_tools_list=True,
)

search_mac_client = search_mac_client_streamable

# 定义百度地图相关的MCP客户端（AK认证）
baidu_map_mcp = MCPServerSse(
    name="百度地图",
    params={ 
        "url": f"https://mcp.map.baidu.com/sse?ak={settings.BAIDUMAP_AK}",
        "timeout": 60,
        "sse_read_timeout": 60 * 30,
    },
    client_session_timeout_seconds=60 * 10,
    cache_tools_list=True,
)

# =======================================================================
# 2. 通用测试执行器(新增:列出工具 -> 查看参数 -> 调用)
# =======================================================================
async def run_mcp_call(
        mcp_instance,
        tool_name: str,
        tool_args: Dict[str, Any]
):
    """
    执行流程:连接 -> 列出所有工具(看参数) -> 调用指定工具 -> 打印结果 -> 断开
    """
    server_name = mcp_instance.name
    print(f"\n{'=' * 60}")
    print(f"[测试启动]服务：{server_name}")
    print(f"{'=' * 60}")

    try:
        # --- 1. 连接 ---
        print(f"[连接]正在连接服务器...")
        await mcp_instance.connect()
        print(f"[连接]成功")

        # --- 2. 列出工具 mcp服务下有多少工具 ---
        print(f"\n[列表]正在获取工具列表及参数定义...")
        tools_list = await mcp_instance.list_tools()

        if tools_list:
            print(f"   发现 {len(tools_list)} 个工具:")
            for i, tool in enumerate(tools_list,1):
                print(f"\n    [{i}]工具名:{tool.name}")
                print(f"       描述:{tool.description}")
                print(f"       参数定义(Schema):")
                #使用 indent=2 让参数结构清晰可见(inputSchema:工具参数(字典))
                print(json.dumps(tool.inputSchema, indent=2, ensure_ascii=False))
        else:
            print(f"   未发现任何工具")

        print(f"\n{'-' * 40}")

        # # --- 3. 调用工具 ---

        # print(f"    发送参数:{json.dumps(tool_args,ensure_ascii=False)}")

        # # 执行核心调用(调用mcp服务中某一个工具)
        # result = await mcp_instance.call_tool(tool_name, tool_args)
        # # print(f"\n[响应]服务器返回结果:")
        # # print(result)

        # # --- 4. 打印结果 ---
        # print(f"\n[响应]服务器返回结果:")
        # for content in result.content:
        #     if hasattr(content, 'text'):

        #         # 尝试解析 JSON 字符串以便美化打印
        #         json_res = json.loads(content.text)
        #         print(json.dumps(json_res, indent=2, ensure_ascii=False))

        #     else:
        #         print(f"[Non-Text]：{content}")

    except Exception as e:
        print(f"\n [异常] 测试失败：{str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # --- 5. 清理 ---
        print(f"\n[断开]正在清理连接...")
        await mcp_instance.cleanup()
        print(f"{server_name} 测试结束\n")

# =======================================================================
# 3. 分别封装的测试函数
# =======================================================================

async def test_bailian_search():
    """
    测试百炼搜索（使用全局 search_mcp）
    """
    await run_mcp_call(
        mcp_instance=search_mac_client,
        tool_name="bailian_web_search", #准备测试联网搜索工具
        tool_args={"query": "北京今天天气如何？"}
    )

async def test_baidu_map():
    """
    测试百度地图MCP
    """
    await run_mcp_call(
        mcp_instance=baidu_map_mcp,
        tool_name="mcp_server_baidu_maps", #准备测试百度地图MCP工具
        tool_args={"query": "北京今天天气如何？"}
    )

# =======================================================================
# 4. 主程序入口
# =======================================================================
async def main():
    # 你可以在这里注释掉不需要跑的测试

    # 任务 1
    # await test_bailian_search()

    # 任务 2
    await test_baidu_map()

if __name__ == "__main__":
    asyncio.run(main())