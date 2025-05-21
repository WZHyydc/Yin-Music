from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from run_recommendation import generate_recommendations

def main():
    # 创建调度器
    scheduler = BlockingScheduler()
    
    # 添加定时任务，每间隔一分钟执行一次
    scheduler.add_job(
        generate_recommendations,
        trigger=IntervalTrigger(minutes=1, timezone=pytz.timezone('Asia/Shanghai')),
        id='generate_recommendations',
        name='生成音乐推荐',
        replace_existing=True
    )
    try:
        print("开始运行推荐服务调度器...")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("停止推荐服务调度器...")
        scheduler.shutdown()

if __name__ == "__main__":
    main() 