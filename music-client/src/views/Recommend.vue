<template>
  <div class="recommend-container">
    <div class="recommend-header">
      <h2>🎵 为你推荐</h2>
      <el-button 
        type="primary" 
        :icon="Refresh" 
        :loading="loading"
        @click="fetchRecommendSongs"
      >
        换一批
      </el-button>
    </div>

    <el-empty 
      v-if="!loading && recommendSongs.length === 0" 
      description="暂无推荐歌曲"
    />

    <div v-else class="recommend-content">
      <el-skeleton :rows="5" animated v-if="loading" />
      
      <template v-else>
        <song-list :songList="recommendSongs" />
        <div class="recommend-tip">
          <el-icon><InfoFilled /></el-icon>
          <span>根据你的听歌喜好，为你推荐这些歌曲</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, computed } from "vue";
import { useStore } from "vuex";
import { Refresh, InfoFilled } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import SongList from "@/components/SongList.vue";
import { HttpManager } from "@/api";

const store = useStore();
const userId = computed(() => store.getters.userId);
const recommendSongs = ref([]);
const loading = ref(false);

async function fetchRecommendSongs() {
  if (!userId.value) {
    ElMessage.warning("请先登录");
    return;
  }

  loading.value = true;
  try {
    // 获取推荐歌曲id
    const songIds = await HttpManager.getRecommendPlayList(userId.value);
    
    if (Array.isArray(songIds)) {
      // 并发获取每首歌的详细信息
      const songDetailPromises = songIds.map((id) => HttpManager.getSongOfId(id));
      const songDetails = await Promise.all(songDetailPromises);
      // 取每个返回的data[0]（假设接口返回数组）
      recommendSongs.value = songDetails.map((item: any) => item.data[0]);
    } else {
      ElMessage.warning("获取推荐歌曲失败");
    }
  } catch (error) {
    console.error(error);
    ElMessage.error("获取推荐歌曲失败，请稍后重试");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchRecommendSongs();
});
</script>

<style lang="scss" scoped>
@import "@/assets/css/var.scss";

.recommend-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.recommend-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  h2 {
    margin: 0;
    color: $color-black;
    font-size: 24px;
  }
}

.recommend-content {
  background-color: $color-white;
  border-radius: $border-radius-songlist;
  padding: 20px;
  min-height: 400px;
}

.recommend-tip {
  margin-top: 20px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 8px;
  
  .el-icon {
    color: #409eff;
  }
}

@media screen and (max-width: $sm) {
  .recommend-container {
    padding: 10px;
  }
  
  .recommend-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
}
</style>