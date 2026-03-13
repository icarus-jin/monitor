<template>
  <div class="device-page">
    <el-breadcrumb separator-class="el-icon-arrow-right" class="breadcrumb">
      <el-breadcrumb-item to="/home">首页</el-breadcrumb-item>
      <el-breadcrumb-item>设备管理</el-breadcrumb-item>
      <el-breadcrumb-item>数据接收</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" class="filter-card">
      <el-row :gutter="12" class="toolbar">
        <el-col :span="6">
          <el-input v-model="searchKeyword" placeholder="输入设备ID/铱星号/传感器标识" clearable @clear="search" @keyup.enter.native="search">
            <el-button slot="append" icon="el-icon-search" @click="search" />
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="searchDateRange"
            type="daterange"
            unlink-panels
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="yyyy-MM-dd"
            size="small"
            style="width: 100%;"
            @change="search"
          />
        </el-col>
        <el-col :span="4">
          <el-select v-model="searchStage" placeholder="处理阶段" clearable @change="search">
            <el-option label="接收失败" value="recv_failed" />
            <el-option label="解析失败" value="parse_failed" />
            <el-option label="入库失败" value="db_failed" />
            <el-option label="处理完成" value="completed" />
          </el-select>
        </el-col>
        <el-col :span="6" class="toolbar-buttons">
          <span class="selected-tip">选中 <b>{{ selectedRows.length }}</b> 条</span>
          <el-button size="mini" type="primary" :disabled="!selectedRows.length">导出</el-button>
          <el-button size="mini" type="success" @click="openSendDialog">测试发送</el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-dialog :title="messageDialogTitle" :visible.sync="messageDialogVisible" width="560px">
      <div class="message-dialog-content">
        {{ messageDialogContent || '-' }}
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button type="primary" @click="messageDialogVisible = false">确 定</el-button>
      </span>
    </el-dialog>

    <el-dialog title="TCP 测试发送" :visible.sync="sendDialogVisible" width="620px">
      <el-form label-width="90px">
        <el-form-item label="目标地址">
          <el-input v-model="sendHost" placeholder="127.0.0.1" />
        </el-form-item>
        <el-form-item label="目标端口">
          <el-input v-model.number="sendPort" placeholder="8088" />
        </el-form-item>
        <el-form-item label="二进制数据">
          <el-input
            v-model="sendPayload"
            type="textarea"
            :rows="6"
            placeholder="输入十六进制，多个包用分号分隔，例如：01 02 03; 0A 0B 0C"
          />
        </el-form-item>
      </el-form>
      <span slot="footer" class="dialog-footer">
        <el-button @click="sendDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="sendLoading" @click="sendPackets">发 送</el-button>
      </span>
    </el-dialog>

    <el-card shadow="never" class="table-card">
      <el-table
        v-loading="tableLoading"
        :data="tableData"
        border
        class="device-table"
        highlight-current-row
        empty-text="暂无数据接收记录"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" align="center" />
        <el-table-column prop="id" label="序号" width="70" />
        <el-table-column prop="ip" label="来源IP" width="130" />
        <el-table-column prop="time" label="请求时间" width="170" />
        <el-table-column prop="device_id" label="设备ID" width="140" />
        <el-table-column prop="iridiumid" label="铱星号" width="120" />
        <el-table-column prop="sn" label="SN" width="80" />
        <el-table-column prop="sensorflag" label="传感器标志位" min-width="140" />
        <el-table-column prop="packet_len" label="包长" width="90" />
        <el-table-column prop="stage" label="处理阶段" width="120">
          <template slot-scope="scope">
            <el-tag :type="_stageTagType(scope.row.stage)" size="small">
              {{ _stageLabel(scope.row.stage) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="处理说明" min-width="180">
          <template slot-scope="scope">
            <el-tooltip class="item" effect="dark" :content="scope.row.message" placement="top">
              <span class="ellipsis-text">{{ scope.row.message || '-' }}</span>
            </el-tooltip>
            <el-button type="text" size="mini" @click="openMessageDialog(scope.row.message, '处理说明')">查看</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="raw" label="原始内容" min-width="200">
          <template slot-scope="scope">
            <el-tooltip class="item" effect="dark" :content="scope.row.raw" placement="top">
              <span class="ellipsis-text">{{ scope.row.raw || '-' }}</span>
            </el-tooltip>
            <el-button type="text" size="mini" @click="openMessageDialog(scope.row.raw, '原始内容')">查看</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="parse_result" label="解析结果" min-width="220">
          <template slot-scope="scope">
            <el-tooltip class="item" effect="dark" :content="scope.row.parse_result" placement="top">
              <span class="ellipsis-text">{{ scope.row.parse_result || '-' }}</span>
            </el-tooltip>
            <el-button type="text" size="mini" @click="openMessageDialog(scope.row.parse_result, '解析结果')">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="pagination"
        background
        layout="total, sizes, prev, pager, next, jumper"
        :current-page="page"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>
  </div>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
export default {
  data () {
    return {
      tableData: [],
      tableLoading: false,
      total: 0,
      page: 1,
      pageSize: 10,
      searchKeyword: '',
      searchDateRange: [],
      searchStage: '',
      selectedRows: [],
      sendDialogVisible: false,
      sendLoading: false,
      sendHost: '127.0.0.1',
      sendPort: 8088,
      sendPayload: '',
      messageDialogVisible: false,
      messageDialogContent: '',
      messageDialogTitle: '处理说明'
    }
  },
  created () {
    this.getTableData()
  },
  methods: {
    handleSelectionChange (rows) {
      this.selectedRows = Array.isArray(rows) ? rows : []
    },
    handleSizeChange (size) {
      this.pageSize = size
      this.page = 1
      this.getTableData()
    },
    handleCurrentChange (page) {
      this.page = page
      this.getTableData()
    },
    search () {
      this.page = 1
      this.getTableData()
    },
    async getTableData () {
      try {
        this.tableLoading = true
        const params = {
          page: this.page,
          page_size: this.pageSize
        }
        if (this.searchKeyword) {
          params.keyword = this.searchKeyword
        }
        if (this.searchDateRange && this.searchDateRange.length === 2) {
          params.start_date = this.searchDateRange[0]
          params.end_date = this.searchDateRange[1]
        }
        if (this.searchStage) {
          params.stage = this.searchStage
        }
        const { data: res } = await this.$axios.get('/receive_log/list/', { params })
        if (res && res.code === 200) {
          const payload = res.data || {}
          const rows = Array.isArray(payload.records) ? payload.records : []
          this.tableData = rows
          this.total = payload.total || 0
        } else {
          this.tableData = []
          this.total = 0
        }
      } catch (e) {
        this.tableData = []
        this.total = 0
      } finally {
        this.tableLoading = false
      }
    },
    openSendDialog () {
      this.sendDialogVisible = true
    },
    async sendPackets () {
      const host = (this.sendHost || '').trim()
      const port = Number(this.sendPort)
      if (!host || !port) {
        this.$message.warning('请填写目标地址和端口')
        return
      }
      const payload = (this.sendPayload || '').trim()
      if (!payload) {
        this.$message.warning('请输入要发送的十六进制数据')
        return
      }
      const packets = payload.split(';').map(item => item.trim()).filter(Boolean)
      if (!packets.length) {
        this.$message.warning('请输入有效的十六进制数据')
        return
      }

      this.sendLoading = true
      try {
        const { data: res } = await this.$axios.post('/receive_log/send_tcp/', {
          host,
          port,
          packets
        })
        if (res && res.code === 200) {
          this.$message.success(res.msg || '发送成功')
          this.sendDialogVisible = false
          this.sendPayload = ''
          this.getTableData()
        } else {
          this.$message.error(res?.msg || '发送失败')
        }
      } catch (e) {
        this.$message.error('发送失败')
      } finally {
        this.sendLoading = false
      }
    },
    openMessageDialog (message, title) {
      this.messageDialogContent = message || ''
      this.messageDialogTitle = title || '处理说明'
      this.messageDialogVisible = true
    },
    _stageLabel (stage) {
      const map = {
        recv_failed: '接收失败',
        parse_failed: '解析失败',
        db_failed: '入库失败',
        completed: '处理完成'
      }
      return map[stage] || stage || '-'
    },
    _stageTagType (stage) {
      const map = {
        recv_failed: 'danger',
        parse_failed: 'danger',
        db_failed: 'warning',
        completed: 'success'
      }
      return map[stage] || 'info'
    }
  }
}
</script>

<style scoped>
.device-page { padding: 22px; min-height: 100vh; font-size: 14px; background: #f1f5f9; }
.breadcrumb { margin-bottom: 14px; }
.filter-card, .table-card { border-radius: 12px; border: 1px solid #e2e8f0; }
.filter-card { margin-bottom: 12px; }
.table-card { margin-bottom: 14px; }
.toolbar { margin-bottom: 0; display: flex; align-items: center; }
.toolbar-buttons { display: flex; justify-content: flex-end; align-items: center; gap: 8px; }
.selected-tip {
  font-size: 12px;
  color: #64748b;
  padding: 4px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
}
.selected-tip b { color: #2563eb; }
.device-table ::v-deep th { background: #f8fafc; color: #334155; font-weight: 600; }
.device-table ::v-deep td { background: #fff; color: #1f2937; }
.device-table ::v-deep tr:hover td { background: #f8fbff; }
.pagination { margin-top: 16px; text-align: right; }
.ellipsis-text {
  display: inline-block;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}
.message-dialog-content {
  white-space: pre-wrap;
  word-break: break-all;
  color: #1f2937;
  line-height: 1.6;
}
</style>
