#!/usr/bin/env python3
"""
Windows 任务计划程序自动配置脚本
自动创建定时推送任务
"""

import os
import sys
import json
import subprocess
from pathlib import Path


def load_schedule_config():
    """加载调度配置"""
    try:
        with open('schedule_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载配置文件失败: {e}")
        return None


def get_python_path():
    """获取Python解释器路径"""
    return sys.executable


def get_project_path():
    """获取项目路径"""
    return str(Path(__file__).parent.absolute())


def create_windows_task(schedule: dict, python_path: str, project_path: str):
    """
    创建Windows任务计划

    Args:
        schedule: 任务配置
        python_path: Python解释器路径
        project_path: 项目路径
    """
    name = schedule.get('name', '未命名任务')
    time_str = schedule.get('time', '09:00')
    weekday = schedule.get('weekday', None)
    description = schedule.get('description', '')

    task_name = f"AI新闻推送-{name}"

    print(f"\n{'=' * 60}")
    print(f"创建任务: {task_name}")
    print(f"推送时间: {time_str}")
    print(f"{'=' * 60}")

    # 构造 schtasks 命令
    cmd = [
        'schtasks',
        '/Create',
        '/TN', task_name,
        '/TR', f'"{python_path}" "{project_path}\\scheduler.py" --now --name "{name}"',
        '/SC', 'DAILY',
        '/ST', time_str,
        '/F'  # 强制创建，覆盖已存在的任务
    ]

    # 如果指定了星期，则只在特定星期执行
    if weekday is not None:
        # 将Python weekday (0-6) 转换为 Windows weekday (MON-SUN)
        weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
        cmd.extend(['/D', weekdays[weekday]])

    try:
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='gbk'  # Windows 中文环境
        )

        if result.returncode == 0:
            print(f"✅ 任务 '{task_name}' 创建成功")
            print(f"   描述: {description}")
            return True
        else:
            print(f"❌ 任务创建失败")
            print(f"   错误: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 创建任务时出错: {e}")
        return False


def list_existing_tasks():
    """列出已存在的AI新闻推送任务"""
    try:
        result = subprocess.run(
            ['schtasks', '/Query', '/FO', 'LIST'],
            capture_output=True,
            text=True,
            encoding='gbk'
        )

        tasks = []
        for line in result.stdout.split('\n'):
            if 'AI新闻推送' in line:
                tasks.append(line.strip())

        if tasks:
            print("\n📋 已存在的AI新闻推送任务:")
            for task in tasks:
                print(f"  - {task}")
        else:
            print("\n💡 当前没有AI新闻推送任务")

    except Exception as e:
        print(f"❌ 查询任务失败: {e}")


def delete_task(task_name: str):
    """删除指定任务"""
    try:
        result = subprocess.run(
            ['schtasks', '/Delete', '/TN', task_name, '/F'],
            capture_output=True,
            text=True,
            encoding='gbk'
        )

        if result.returncode == 0:
            print(f"✅ 任务 '{task_name}' 已删除")
            return True
        else:
            print(f"❌ 删除任务失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 删除任务时出错: {e}")
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("🪟 Windows 任务计划程序配置工具")
    print("=" * 70)

    # 检查操作系统
    if sys.platform != 'win32':
        print("❌ 此脚本仅支持Windows系统")
        print("💡 macOS/Linux 用户请使用 crontab，参考 SCHEDULE_GUIDE.md")
        return

    # 检查是否以管理员身份运行
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        print("\n⚠️  警告：建议以管理员身份运行此脚本")
        print("   右键点击 PowerShell → 以管理员身份运行")
        response = input("\n是否继续? (y/n): ")
        if response.lower() != 'y':
            return

    # 加载配置
    config = load_schedule_config()
    if not config:
        return

    # 获取路径
    python_path = get_python_path()
    project_path = get_project_path()

    print(f"\n📍 Python路径: {python_path}")
    print(f"📁 项目路径: {project_path}")

    # 列出已存在的任务
    list_existing_tasks()

    # 显示将要创建的任务
    schedules = [s for s in config.get('schedules', []) if s.get('enabled', True)]

    print(f"\n📋 将创建 {len(schedules)} 个任务:")
    for i, schedule in enumerate(schedules, 1):
        name = schedule.get('name', '未命名')
        time = schedule.get('time', '')
        topics = ', '.join(schedule.get('topics', []))
        print(f"  {i}. {name} - {time} - 主题: {topics}")

    response = input(f"\n是否开始创建任务? (y/n): ")
    if response.lower() != 'y':
        print("❌ 已取消")
        return

    # 创建任务
    print("\n" + "=" * 70)
    print("开始创建任务...")
    print("=" * 70)

    success_count = 0
    for schedule in schedules:
        if create_windows_task(schedule, python_path, project_path):
            success_count += 1

    # 总结
    print("\n" + "=" * 70)
    print(f"✅ 成功创建 {success_count}/{len(schedules)} 个任务")
    print("=" * 70)

    if success_count > 0:
        print("\n💡 后续操作:")
        print("  1. 打开任务计划程序 (运行: taskschd.msc)")
        print("  2. 找到创建的任务，右键 → 运行，测试是否正常")
        print("  3. 查看任务历史记录，检查执行情况")
        print("  4. 查看 scheduler.log 日志文件")

    print("\n📚 详细文档: SCHEDULE_GUIDE.md")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
