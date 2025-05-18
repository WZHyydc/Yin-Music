from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from run_recommendation import generate_recommendations

def main():
    # 创建调度器
    scheduler = BlockingScheduler()
    
    # 添加定时任务，每天凌晨2点执行
    scheduler.add_job(
        generate_recommendations,
        trigger=CronTrigger(hour=2, minute=0),
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