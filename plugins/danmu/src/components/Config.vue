<template>
  <div class="plugin-config">
    <v-card flat class="rounded border">
      <!-- 标题区域 -->
      <v-card-title class="text-subtitle-1 d-flex align-center px-3 py-2 bg-primary-lighten-5">
        <v-icon icon="mdi-cog" class="mr-2" color="primary" size="small" />
        <span>弹幕刮削配置</span>
      </v-card-title>
      
      <v-card-text class="px-3 py-2">
        <v-alert v-if="error" type="error" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ error }}</v-alert>
        <v-alert v-if="successMessage" type="success" density="compact" class="mb-2 text-caption" variant="tonal" closable>{{ successMessage }}</v-alert>

        <v-form ref="form" v-model="isFormValid" @submit.prevent="saveFullConfig">
          <!-- 基本设置卡片 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-tune" class="mr-2" color="primary" size="small" />
              <span>基本设置</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-row>
                <v-col cols="12">
                  <v-select
                    v-model="editableConfig.data_source"
                    label="数据源"
                    variant="outlined"
                    :items="[
                      { title: '弹弹play（默认）', value: 'dandanplay' },
                      { title: 'danmu_api（扩展源）', value: 'danmu_api' },
                      { title: '混合（弹弹play + danmu_api）', value: 'hybrid' }
                    ]"
                    hint="danmu_api 覆盖国产剧/欧美剧/韩剧/真人电影/综艺；弹弹play 覆盖动画/日剧"
                    persistent-hint
                    prepend-inner-icon="mdi-database-sync"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-power" size="small" :color="editableConfig.enable ? 'success' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">启用插件</div>
                          <div class="text-caption text-grey">是否启用弹幕刮削功能</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.enable"
                          color="primary"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-bilibili" size="small" :color="editableConfig.onlyFromBili ? 'info' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">优先使用B站弹幕</div>
                          <div class="text-caption text-grey">B站弹幕不足时自动回退全部来源</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.onlyFromBili"
                          color="info"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6" v-if="editableConfig.data_source !== 'danmu_api'">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-database" size="small" :color="editableConfig.useTmdbID ? 'info' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">使用TMDB ID</div>
                          <div class="text-caption text-grey">是否使用TMDB ID进行匹配</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.useTmdbID"
                          color="info"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6" v-if="editableConfig.data_source !== 'dandanplay'">
                  <v-text-field
                    v-model="editableConfig.danmu_api_url"
                    label="danmu_api 服务地址"
                    variant="outlined"
                    placeholder="http://192.168.123.146:9321"
                    hint="danmu_api 服务地址，不带 /api 后缀"
                    persistent-hint
                    prepend-inner-icon="mdi-server-network"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6" v-if="editableConfig.data_source !== 'dandanplay'">
                  <v-text-field
                    v-model="editableConfig.danmu_api_token"
                    label="danmu_api TOKEN"
                    variant="outlined"
                    placeholder="留空使用默认 TOKEN"
                    hint="自定义 TOKEN，留空则 URL 不带 token 段"
                    persistent-hint
                    prepend-inner-icon="mdi-key-variant"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6" v-if="editableConfig.data_source === 'hybrid'">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-swap-horizontal" size="small" :color="editableConfig.danmu_api_priority ? 'info' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">danmu_api 优先</div>
                          <div class="text-caption text-grey">开启后先查 danmu_api，未命中再回退弹弹play</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.danmu_api_priority"
                          color="info"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-auto-fix" size="small" :color="editableConfig.auto_scrape ? 'success' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">入库自动刮削</div>
                          <div class="text-caption text-grey">是否在媒体入库时自动刮削弹幕</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.auto_scrape"
                          color="success"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-repeat" size="small" :color="editableConfig.enable_retry_task ? 'warning' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div>
                          <div class="text-subtitle-2">启用重试任务</div>
                          <div class="text-caption text-grey">弹幕数量不足时自动加入重试列表</div>
                        </div>
                        <v-switch
                          v-model="editableConfig.enable_retry_task"
                          color="warning"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
                <v-col cols="12" md="6">
                  <div class="setting-item d-flex align-center py-2">
                    <v-icon icon="mdi-file-video-outline" size="small" :color="editableConfig.enable_strm ? 'info' : 'grey'" class="mr-3"></v-icon>
                    <div class="setting-content flex-grow-1">
                      <div class="d-flex justify-space-between align-center">
                        <div class="d-flex align-center">
                          <div>
                            <div class="text-subtitle-2">启用STRM文件刮削</div>
                            <div class="text-caption text-grey">是否支持.strm流媒体文件的弹幕刮削</div>
                            <div class="text-caption text-orange" v-if="editableConfig.data_source !== 'dandanplay'">danmu_api 靠文件名匹配，strm 无 TMDB 时也可用</div>
                          </div>
                          <v-tooltip location="top">
                            <template v-slot:activator="{ props }">
                              <v-btn
                                v-bind="props"
                                icon="mdi-help-circle-outline"
                                size="x-small"
                                variant="text"
                                color="grey"
                                class="ml-2"
                              ></v-btn>
                            </template>
                            <div class="tooltip-content">
                              <div class="text-subtitle-2 mb-1">STRM文件刮削说明</div>
                              <div class="text-caption">
                                <div class="mb-1"><strong>功能限制：</strong></div>
                                <div>• 仅支持TMDB ID匹配，无法使用文件hash</div>
                                <div>• 无法提取内嵌字幕，仅支持外部字幕</div>
                                <div>• 使用默认分辨率(1920x1080)</div>
                                <div class="mt-2 mb-1"><strong>使用条件：</strong></div>
                                <div>• 文件名需包含正确的媒体信息</div>
                                <div>• MoviePilot能够识别并获取TMDB ID</div>
                                <div>• 弹弹play平台需要有对应弹幕资源</div>
                              </div>
                            </div>
                          </v-tooltip>
                        </div>
                        <v-switch
                          v-model="editableConfig.enable_strm"
                          color="info"
                          inset
                          :disabled="saving"
                          density="compact"
                          hide-details
                          class="small-switch"
                        ></v-switch>
                      </div>
                    </div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 弹幕参数设置 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-video" class="mr-2" color="primary" size="small" />
              <span>弹幕参数设置</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.fontsize"
                    label="字体大小"
                    type="number"
                    variant="outlined"
                    :min="1"
                    :rules="[v => v > 0 || '字体大小必须大于0']"
                    hint="弹幕字体大小"
                    persistent-hint
                    prepend-inner-icon="mdi-format-font-size-increase"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="editableConfig.screen_area"
                    label="弹幕显示区域"
                    variant="outlined"
                    :items="[
                      { title: '全屏弹幕', value: 'full' },
                      { title: '半屏弹幕', value: 'half' },
                      { title: '1/4屏弹幕', value: 'quarter' }
                    ]"
                    hint="选择弹幕显示的屏幕区域，超出区域的弹幕将被忽略"
                    persistent-hint
                    prepend-inner-icon="mdi-monitor"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-select>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.alpha"
                    label="透明度"
                    type="number"
                    variant="outlined"
                    :min="0"
                    :max="1"
                    :step="0.1"
                    :rules="[v => v >= 0 && v <= 1 || '透明度必须在0-1之间']"
                    hint="弹幕透明度(0-1)"
                    persistent-hint
                    prepend-inner-icon="mdi-opacity"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.duration"
                    label="持续时间"
                    type="number"
                    variant="outlined"
                    :min="1"
                    :rules="[v => v > 0 || '持续时间必须大于0']"
                    hint="弹幕显示持续时间(秒)"
                    persistent-hint
                    prepend-inner-icon="mdi-clock-outline"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.max_same_screen"
                    label="同屏弹幕上限"
                    type="number"
                    variant="outlined"
                    :min="0"
                    :rules="[v => (v === '' || v === null || (Number.isInteger(Number(v)) && Number(v) >= 0)) || '必须为 0 或正整数']"
                    hint="0=不限制；建议 10~30，降低同屏密度可显著改善播放流畅度"
                    persistent-hint
                    prepend-inner-icon="mdi-layers-triple-outline"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model.number="editableConfig.max_threads"
                    label="刮削并发数"
                    type="number"
                    variant="outlined"
                    :min="1"
                    :max="32"
                    :rules="[v => (v >= 1 && v <= 32) || '并发数必须在1-32之间']"
                    hint="同时处理的文件数(1-32)，只影响本机开销，对弹弹play的请求另有限速"
                    persistent-hint
                    prepend-inner-icon="mdi-animation-outline"
                    :disabled="saving"
                    density="compact"
                    class="text-caption"
                  ></v-text-field>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- 刮削路径设置 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-title class="text-caption d-flex align-center px-3 py-2 bg-primary-lighten-5">
              <v-icon icon="mdi-folder" class="mr-2" color="primary" size="small" />
              <span>手动控制媒体库路径</span>
            </v-card-title>
            <v-card-text class="px-3 py-2">
              <v-textarea
                v-model="editableConfig.path"
                label="/"
                variant="outlined"
                hint="每行一个路径,在状态页手动控制刮削"
                persistent-hint
                prepend-inner-icon="mdi-folder-multiple"
                :disabled="saving"
                density="compact"
                class="text-caption"
                rows="3"
              ></v-textarea>
            </v-card-text>
          </v-card>

          <!-- 帮助信息卡片 -->
          <v-card flat class="rounded mb-3 border config-card">
            <v-card-text class="d-flex align-center px-3 py-2">
              <v-icon icon="mdi-information" color="info" class="mr-2" size="small"></v-icon>
              <span class="text-caption">
                此插件用于生成视频的弹幕字幕文件.弹幕来源为弹弹play平台；数据源选择 danmu_api/混合 时可从扩展源补充国剧/欧美/韩剧/真人电影/综艺弹幕.
              </span>
            </v-card-text>
          </v-card>
        </v-form>
      </v-card-text>
      
      <v-divider></v-divider>
      
      <v-card-actions class="px-2 py-1">
        <v-btn color="info" @click="emit('switch')" prepend-icon="mdi-view-dashboard" :disabled="saving" variant="text" size="small">状态页</v-btn>
        <v-spacer></v-spacer>
        <v-btn color="secondary" variant="text" @click="resetConfigToFetched" :disabled="!initialConfigLoaded || saving" prepend-icon="mdi-restore" size="small">重置</v-btn>
        <v-btn color="primary" :disabled="!isFormValid || saving" @click="saveFullConfig" :loading="saving" prepend-icon="mdi-content-save" variant="text" size="small">保存配置</v-btn>
        <v-btn color="grey" @click="emit('close')" prepend-icon="mdi-close" :disabled="saving" variant="text" size="small">关闭</v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

const props = defineProps({
  api: { 
    type: [Object, Function],
    required: true,
  },
  initialConfig: {
    type: Object,
    default: () => ({}),
  }
});

const emit = defineEmits(['close', 'switch', 'config-updated-on-server', 'save']);

const form = ref(null);
const isFormValid = ref(true);
const error = ref(null);
const successMessage = ref(null);
const saving = ref(false);
const initialConfigLoaded = ref(false);

// Holds the config as fetched from server, used for reset
const serverFetchedConfig = reactive({}); 

// Holds the config being edited in the form
const editableConfig = reactive({
  enable: false,
  width: 1920,
  height: 1080,
  fontsize: 50,
  alpha: 0.8,
  duration: 15,
  path: '',
  max_threads: 10,
  onlyFromBili: false,
  useTmdbID: true,
  data_source: 'dandanplay',
  danmu_api_url: 'http://192.168.123.146:9321',
  danmu_api_token: '',
  danmu_api_priority: false,
  auto_scrape: true,
  enable_retry_task: true,
  screen_area: 'full',
  max_same_screen: 0,
  enable_strm: true
});

// 同屏弹幕上限归一化：0=不限制，其余取非负整数（与后端 _clamp_max_same_screen 对齐）
function normalizeMaxSameScreen(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 0) return 0;
  return Math.floor(n);
}

const getPluginId = () => {
  return "Danmu";
};

async function loadInitialData() {
  error.value = null;
  saving.value = true;
  initialConfigLoaded.value = false;
  
  try {
    const pluginId = getPluginId();
    if (!pluginId) { 
      throw new Error('获取插件ID失败'); 
    }
    
    const data = await props.api.get(`plugin/${pluginId}/config`);
    
    if (data) {
      // 更新服务器配置
      Object.assign(serverFetchedConfig, JSON.parse(JSON.stringify(data)));
      // 更新编辑中的配置
      Object.assign(editableConfig, {
        enable: data.enabled,
        width: data.width,
        height: data.height,
        fontsize: data.fontsize,
        alpha: data.alpha,
        duration: data.duration,
        path: data.path,
        max_threads: data.max_threads,
        onlyFromBili: data.onlyFromBili,
        useTmdbID: data.useTmdbID,
        data_source: data.data_source,
        danmu_api_url: data.danmu_api_url,
        danmu_api_token: data.danmu_api_token,
        danmu_api_priority: data.danmu_api_priority,
        auto_scrape: data.auto_scrape,
        enable_retry_task: data.enable_retry_task,
        screen_area: data.screen_area,
        max_same_screen: normalizeMaxSameScreen(data.max_same_screen),
        enable_strm: data.enable_strm
      });
      initialConfigLoaded.value = true;
      successMessage.value = '成功加载配置';
    } else {
      throw new Error('加载配置失败');
    }
  } catch (err) {
    console.error('加载配置失败:', err);
    error.value = err.message || '加载配置失败，请检查网络或API';
    // 使用初始配置
    if (props.initialConfig) {
      Object.assign(serverFetchedConfig, JSON.parse(JSON.stringify(props.initialConfig)));
      Object.assign(editableConfig, {
        enable: props.initialConfig.enabled,
        width: props.initialConfig.width,
        height: props.initialConfig.height,
        fontsize: props.initialConfig.fontsize,
        alpha: props.initialConfig.alpha,
        duration: props.initialConfig.duration,
        path: props.initialConfig.path,
        max_threads: props.initialConfig.max_threads,
        onlyFromBili: props.initialConfig.onlyFromBili,
        useTmdbID: props.initialConfig.useTmdbID,
        data_source: props.initialConfig.data_source,
        danmu_api_url: props.initialConfig.danmu_api_url,
        danmu_api_token: props.initialConfig.danmu_api_token,
        danmu_api_priority: props.initialConfig.danmu_api_priority,
        auto_scrape: props.initialConfig.auto_scrape,
        enable_retry_task: props.initialConfig.enable_retry_task,
        screen_area: props.initialConfig.screen_area,
        max_same_screen: normalizeMaxSameScreen(props.initialConfig.max_same_screen),
        enable_strm: props.initialConfig.enable_strm
      });
    }
    successMessage.value = null;
  } finally {
    saving.value = false;
    setTimeout(() => { successMessage.value = null; error.value = null; }, 4000);
  }
}

async function saveFullConfig() {
  error.value = null;
  successMessage.value = null;
  if (!form.value) return;
  
  const validation = await form.value.validate();
  if (!validation.valid) {
    error.value = '请检查表单中的错误';
    return;
  }

  saving.value = true;

  try {
    const pluginId = getPluginId();
    if (!pluginId) {
      throw new Error('获取插件ID失败');
    }

    // 转换配置格式
    const configToSave = {
      enabled: editableConfig.enable,
      width: editableConfig.width,
      height: editableConfig.height,
      fontsize: editableConfig.fontsize,
      alpha: editableConfig.alpha,
      duration: editableConfig.duration,
      path: editableConfig.path,
      max_threads: editableConfig.max_threads,
      onlyFromBili: editableConfig.onlyFromBili,
      useTmdbID: editableConfig.useTmdbID,
      data_source: editableConfig.data_source,
      danmu_api_url: editableConfig.danmu_api_url,
      danmu_api_token: editableConfig.danmu_api_token,
      danmu_api_priority: editableConfig.danmu_api_priority,
      auto_scrape: editableConfig.auto_scrape,
      enable_retry_task: editableConfig.enable_retry_task,
      screen_area: editableConfig.screen_area,
      max_same_screen: normalizeMaxSameScreen(editableConfig.max_same_screen),
      enable_strm: editableConfig.enable_strm
    };

    // 发送保存请求
    const result = await props.api.post(`plugin/${pluginId}/config`, configToSave);
    
    if (result && result.success) {
      // 更新服务器配置
      Object.assign(serverFetchedConfig, JSON.parse(JSON.stringify(configToSave)));
      successMessage.value = '配置已保存';
      emit('config-updated-on-server');
    } else {
      throw new Error(result?.message || '保存配置失败');
    }
  } catch (err) {
    console.error('保存配置失败:', err);
    error.value = err.message || '保存配置失败，请检查网络或查看日志';
  } finally {
    saving.value = false;
    setTimeout(() => { 
      successMessage.value = null; 
      if (error.value && !error.value.startsWith('保存配置失败') && !error.value.startsWith('配置已部分保存')) { 
        error.value = null; 
      }
    }, 5000); 
  }
}

function resetConfigToFetched() {
  if (initialConfigLoaded.value) {
    Object.assign(editableConfig, {
      enable: serverFetchedConfig.enabled,
      width: serverFetchedConfig.width,
      height: serverFetchedConfig.height,
      fontsize: serverFetchedConfig.fontsize,
      alpha: serverFetchedConfig.alpha,
      duration: serverFetchedConfig.duration,
      path: serverFetchedConfig.path,
      max_threads: serverFetchedConfig.max_threads,
      onlyFromBili: serverFetchedConfig.onlyFromBili,
      useTmdbID: serverFetchedConfig.useTmdbID,
      data_source: serverFetchedConfig.data_source,
      danmu_api_url: serverFetchedConfig.danmu_api_url,
      danmu_api_token: serverFetchedConfig.danmu_api_token,
      danmu_api_priority: serverFetchedConfig.danmu_api_priority,
      auto_scrape: serverFetchedConfig.auto_scrape,
      enable_retry_task: serverFetchedConfig.enable_retry_task,
      screen_area: serverFetchedConfig.screen_area,
      max_same_screen: normalizeMaxSameScreen(serverFetchedConfig.max_same_screen),
      enable_strm: serverFetchedConfig.enable_strm
    });
    error.value = null;
    successMessage.value = '配置已重置为上次加载的状态';
    if (form.value) form.value.resetValidation();
  } else {
    error.value = '重置失败';
  }
  setTimeout(() => { successMessage.value = null; error.value = null; }, 3000);
}

onMounted(() => {
  // 初始化时使用初始配置
  if (props.initialConfig) {
    Object.assign(serverFetchedConfig, JSON.parse(JSON.stringify(props.initialConfig)));
    Object.assign(editableConfig, {
      enable: props.initialConfig.enabled,
      width: props.initialConfig.width,
      height: props.initialConfig.height,
      fontsize: props.initialConfig.fontsize,
      alpha: props.initialConfig.alpha,
      duration: props.initialConfig.duration,
      path: props.initialConfig.path,
      max_threads: props.initialConfig.max_threads,
      onlyFromBili: props.initialConfig.onlyFromBili,
      useTmdbID: props.initialConfig.useTmdbID,
      auto_scrape: props.initialConfig.auto_scrape,
      enable_retry_task: props.initialConfig.enable_retry_task,
      screen_area: props.initialConfig.screen_area,
      max_same_screen: normalizeMaxSameScreen(props.initialConfig.max_same_screen),
      enable_strm: props.initialConfig.enable_strm
    });
  }
  loadInitialData();
});
</script>

<style scoped>
.plugin-config {
  max-width: 80rem;
  margin: 0 auto;
  padding: 0.5rem;
}

.bg-primary-lighten-5 {
  background-color: rgba(var(--v-theme-primary), 0.07);
}

.border {
  border: thin solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.config-card {
  background-image: linear-gradient(to right, rgba(var(--v-theme-surface), 0.98), rgba(var(--v-theme-surface), 0.95)), 
                    repeating-linear-gradient(45deg, rgba(var(--v-theme-primary), 0.03), rgba(var(--v-theme-primary), 0.03) 10px, transparent 10px, transparent 20px);
  background-attachment: fixed;
  box-shadow: 0 1px 2px rgba(var(--v-border-color), 0.05) !important;
  transition: all 0.3s ease;
}

.config-card:hover {
  box-shadow: 0 3px 6px rgba(var(--v-border-color), 0.1) !important;
}

.setting-item {
  border-radius: 8px;
  transition: all 0.2s ease;
  padding: 0.5rem;
  margin-bottom: 4px;
}

.setting-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.03);
}

.small-switch {
  transform: scale(0.8);
  margin-right: -8px;
}

.text-subtitle-2 {
  font-size: 14px !important;
  font-weight: 500;
  margin-bottom: 2px;
}

.tooltip-content {
  max-width: 350px;
  padding: 4px;
  line-height: 1.4;
}

.tooltip-content .text-caption {
  color: rgba(255, 255, 255, 0.87);
}

.tooltip-content strong {
  color: rgba(255, 255, 255, 0.95);
}

.tooltip-content div {
  margin-bottom: 2px;
}
</style>
