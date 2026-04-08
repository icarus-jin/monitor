<template>
  <div class="email-page">
    <el-card class="email-card" shadow="never">
      <div class="card-title">邮箱管理</div>

      <el-form :inline="true" :model="loginForm" class="login-form">
        <el-form-item label="邮箱">
          <el-input v-model="loginForm.email" placeholder="请输入邮箱" size="small" />
        </el-form-item>
        <el-form-item label="授权码">
          <el-input v-model="loginForm.password" placeholder="请输入授权码" size="small" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" size="small" :loading="loginLoading" @click="handleLogin">登录</el-button>
        </el-form-item>
      </el-form>

      <el-divider />

      <div class="query-row">
        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间(GMT)"
          end-placeholder="结束时间(GMT)"
          value-format="yyyy-MM-dd HH:mm:ss"
          size="small"
        />
        <el-button type="primary" size="small" :loading="listLoading" @click="fetchEmails(1)">查询</el-button>
        <el-button size="small" @click="resetSelection">取消全选</el-button>
        <el-button size="small" @click="selectAll">全选</el-button>
        <el-button type="success" size="small" :loading="downloadLoading" @click="downloadSelected">下载附件</el-button>
        <el-button type="danger" size="small" :loading="deleteLoading" @click="deleteDownloaded">删除已下载</el-button>
      </div>

      <div v-if="downloadInProgress" class="download-progress">
        <el-progress :percentage="downloadProgress" :stroke-width="8" status="success" />
      </div>

      <el-table
        ref="emailTable"
        :data="emailList"
        border
        size="small"
        @selection-change="handleSelectionChange"
        class="email-table"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column label="日期" prop="date" width="180" />
        <el-table-column label="发件人" prop="from" min-width="220" />
        <el-table-column label="主题" prop="subject" min-width="260" />
        <el-table-column label="正文" width="120">
          <template slot-scope="scope">
            <el-button type="text" size="small" @click="openContent(scope.row)">
              查看正文
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-row">
        <div class="pagination-info">第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 封邮件</div>
        <el-pagination
          layout="sizes, prev, pager, next, jumper"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          :page-sizes="pageSizes"
          @current-change="fetchEmails"
          @size-change="handlePageSizeChange"
        />
      </div>

      <el-divider />

      <div class="log-panel">
        <div class="log-title">执行日志</div>
        <div class="log-body">
          <div v-for="(item, idx) in logs" :key="idx" class="log-line">{{ item }}</div>
        </div>
      </div>
    </el-card>

    <el-dialog
      title="邮件正文"
      :visible.sync="contentDialogVisible"
      width="720px"
      :close-on-click-modal="false"
    >
      <div class="email-content-dialog" v-loading="contentLoading">
        <div v-if="contentLoading">加载中...</div>
        <div v-else>{{ currentContent || '暂无正文' }}</div>
      </div>
      <span slot="footer" class="dialog-footer">
        <el-button size="small" @click="contentDialogVisible = false">关闭</el-button>
      </span>
    </el-dialog>
  </div>
</template>

<script>
export default {
  name: 'EmailManage',
  data () {
    return {
      loginForm: {
        email: '',
        password: ''
      },
      loginLoading: false,
      listLoading: false,
      downloadLoading: false,
      deleteLoading: false,
      contentDialogVisible: false,
      contentLoading: false,
      currentContent: '',
      downloadInProgress: false,
      downloadProgress: 0,
      downloadTimer: null,
      allSelected: false,
      emailList: [],
      selectedRows: [],
      allEmailIds: [],
      total: 0,
      page: 1,
      pageSize: 20,
      pageSizes: [10, 20, 50, 100],
      totalPages: 1,
      dateRange: [],
      logs: []
    }
  },
  created () {
    const end = new Date()
    const start = new Date()
    start.setMonth(start.getMonth() - 1)
    this.dateRange = [this.formatDateTimeToGmt(start), this.formatDateTimeToGmt(end)]
  },
  methods: {
    formatDateTimeToGmt (d) {
      const gmt = new Date(d.getTime() - d.getTimezoneOffset() * 60000)
      const yyyy = gmt.getUTCFullYear()
      const mm = String(gmt.getUTCMonth() + 1).padStart(2, '0')
      const dd = String(gmt.getUTCDate()).padStart(2, '0')
      const hh = String(gmt.getUTCHours()).padStart(2, '0')
      const mi = String(gmt.getUTCMinutes()).padStart(2, '0')
      const ss = String(gmt.getUTCSeconds()).padStart(2, '0')
      return `${yyyy}-${mm}-${dd} ${hh}:${mi}:${ss}`
    },
    log (msg) {
      const time = new Date().toLocaleTimeString()
      this.logs.unshift(`[${time}] ${msg}`)
    },
    async handleLogin () {
      if (!this.loginForm.email || !this.loginForm.password) {
        this.$message.warning('请填写邮箱与授权码')
        return
      }
      this.loginLoading = true
      try {
        const { data: res } = await this.$axios.post('/email/login/', {
          email: this.loginForm.email,
          password: this.loginForm.password
        })
        if (res.code !== 200) {
          this.$message.error(res.msg || '登录失败')
          this.log(`登录失败：${res.msg || '未知错误'}`)
          return
        }
        this.$message.success('登录成功')
        this.log('登录成功')
        this.fetchEmails(1)
      } catch (e) {
        this.$message.error('登录失败')
        this.log(`登录异常：${e.message || e}`)
      } finally {
        this.loginLoading = false
      }
    },
    async fetchEmails (page = 1) {
      if (!this.loginForm.email) {
        this.$message.warning('请先登录邮箱')
        return
      }
      if (!this.dateRange || this.dateRange.length !== 2) {
        this.$message.warning('请选择日期范围')
        return
      }
      this.page = page
      this.listLoading = true
      try {
        const { data: res } = await this.$axios.post('/email/list/', {
          email: this.loginForm.email,
          start_date: this.dateRange[0],
          end_date: this.dateRange[1],
          page: this.page,
          page_size: this.pageSize
        })
        if (res.code !== 200) {
          this.$message.error(res.msg || '查询失败')
          this.log(`查询失败：${res.msg || '未知错误'}`)
          return
        }
        const data = res.data || {}
        this.emailList = (data.emails || []).map(item => ({
          ...item,
          _content: ''
        }))
        this.allEmailIds = data.all_ids || []
        this.total = data.total || 0
        this.totalPages = Math.max(1, Math.ceil(this.total / this.pageSize))
        if (this.allSelected) {
          this.selectedRows = this.allEmailIds.map(id => ({ id }))
        }
        this.log(`查询完成，共 ${this.total} 封邮件`)
      } catch (e) {
        this.$message.error('查询失败')
        this.log(`查询异常：${e.message || e}`)
      } finally {
        this.listLoading = false
      }
    },
    handleSelectionChange (rows) {
      this.selectedRows = rows
    },
    handlePageSizeChange (size) {
      this.pageSize = size
      this.fetchEmails(1)
    },
    async selectAll () {
      if (!this.allEmailIds.length) {
        this.$message.warning('暂无可选择的邮件')
        return
      }
      this.allSelected = true
      this.selectedRows = this.allEmailIds.map(id => ({ id }))
      if (this.$refs.emailTable) {
        this.$refs.emailTable.clearSelection()
        this.$nextTick(() => {
          this.$refs.emailTable.toggleAllSelection()
        })
      }
      this.$message.success(`已选中全部 ${this.allEmailIds.length} 封邮件`)
    },
    resetSelection () {
      this.allSelected = false
      this.selectedRows = []
      if (this.$refs.emailTable) {
        this.$refs.emailTable.clearSelection()
      }
    },
    startDownloadProgress () {
      this.downloadInProgress = true
      this.downloadProgress = 10
      if (this.downloadTimer) {
        clearInterval(this.downloadTimer)
      }
      this.downloadTimer = setInterval(() => {
        if (this.downloadProgress < 90) {
          this.downloadProgress += Math.max(1, Math.floor((90 - this.downloadProgress) / 8))
        }
      }, 500)
    },
    stopDownloadProgress (success) {
      if (this.downloadTimer) {
        clearInterval(this.downloadTimer)
        this.downloadTimer = null
      }
      this.downloadProgress = success ? 100 : 0
      setTimeout(() => {
        this.downloadInProgress = false
        if (!success) {
          this.downloadProgress = 0
        }
      }, success ? 600 : 200)
    },
    async openContent (row) {
      this.contentDialogVisible = true
      this.contentLoading = true
      if (row._content) {
        this.currentContent = row._content
        this.contentLoading = false
        return
      }
      try {
        const { data: res } = await this.$axios.post('/email/detail/', {
          email: this.loginForm.email,
          email_id: row.id
        })
        if (res.code !== 200) {
          this.$message.error(res.msg || '正文获取失败')
          this.currentContent = ''
          return
        }
        row._content = res.data && res.data.content ? res.data.content : ''
        this.currentContent = row._content
      } catch (e) {
        this.$message.error('正文获取失败')
        this.currentContent = ''
      } finally {
        this.contentLoading = false
      }
    },
    async downloadSelected () {
      if (!this.selectedRows.length) {
        this.$message.warning('请选择邮件')
        return
      }
      this.downloadLoading = true
      this.startDownloadProgress()
      try {
        const emailIds = this.selectedRows.map(row => row.id)
        const { data: res } = await this.$axios.post('/email/download/', {
          email: this.loginForm.email,
          email_ids: emailIds
        })
        if (res.code !== 200) {
          this.$message.error(res.msg || '下载失败')
          this.log(`下载失败：${res.msg || '未知错误'}`)
          this.stopDownloadProgress(false)
          return
        }
        const stats = (res.data && res.data.stats) || {}
        this.log(`下载完成：邮件[成功 ${stats.success_emails || 0} / 失败 ${stats.failed_emails || 0} / 跳过 ${stats.skipped_emails || 0}]，附件[成功 ${stats.success_attachments || 0} / 跳过 ${stats.skipped_attachments || 0}]`)
        await this.downloadPackage(emailIds)
        this.stopDownloadProgress(true)
        this.$message.success('下载完成')
      } catch (e) {
        this.$message.error('下载失败')
        this.log(`下载异常：${e.message || e}`)
        this.stopDownloadProgress(false)
      } finally {
        this.downloadLoading = false
      }
    },
    async downloadPackage (emailIds) {
      try {
        const response = await this.$axios.post('/email/download_package/', {
          email: this.loginForm.email,
          email_ids: emailIds
        }, { responseType: 'blob' })

        const blob = new Blob([response.data], { type: 'application/zip' })
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        const disposition = response.headers && (response.headers['content-disposition'] || response.headers['Content-Disposition'])
        const match = disposition && /filename\*=UTF-8''([^;]+)/i.exec(disposition)
        link.download = match ? decodeURIComponent(match[1]) : 'attachments.zip'
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
      } catch (e) {
        this.$message.error('附件打包下载失败')
      }
    },
    async deleteDownloaded () {
      if (!this.selectedRows.length) {
        this.$message.warning('请选择邮件')
        return
      }
      this.$confirm('确定删除已下载邮件吗？此操作不可恢复。', '提示', {
        type: 'warning'
      }).then(async () => {
        this.deleteLoading = true
        try {
          const emailIds = this.selectedRows.map(row => row.id)
          const { data: res } = await this.$axios.post('/email/delete_downloaded/', {
            email: this.loginForm.email,
            email_ids: emailIds
          })
          if (res.code !== 200) {
            this.$message.error(res.msg || '删除失败')
            this.log(`删除失败：${res.msg || '未知错误'}`)
            return
          }
          const results = (res.data && res.data.results) || {}
          this.log(`删除完成：成功 ${results.deleted || 0} / 跳过 ${results.skipped || 0} / 失败 ${results.failed || 0}`)
          this.$message.success('删除完成')
          this.fetchEmails(this.page)
        } catch (e) {
          this.$message.error('删除失败')
          this.log(`删除异常：${e.message || e}`)
        } finally {
          this.deleteLoading = false
        }
      }).catch(() => {})
    }
  }
}
</script>

<style scoped>
.email-page {
  padding: 4px;
}

.email-card {
  border-radius: 12px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 10px;
}

.login-form {
  margin-bottom: 8px;
}

.query-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 12px;
}

.email-table {
  margin-top: 8px;
}

.email-content-dialog {
  padding: 8px 12px;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  white-space: pre-wrap;
  max-height: 400px;
  overflow-y: auto;
}

.download-progress {
  margin: 8px 0 0;
}

.pagination-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 12px;
}

.pagination-info {
  font-size: 12px;
  color: #6b7280;
}

.log-panel {
  background: #0f172a;
  color: #e2e8f0;
  padding: 10px;
  border-radius: 8px;
}

.log-title {
  font-size: 12px;
  margin-bottom: 6px;
  color: #93c5fd;
}

.log-body {
  max-height: 260px;
  overflow-y: auto;
  font-size: 12px;
  line-height: 1.4;
}

.log-line {
  margin-bottom: 4px;
}
</style>
