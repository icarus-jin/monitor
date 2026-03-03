<template>
  <div class="user-page">
    <el-breadcrumb separator-class="el-icon-arrow-right" class="breadcrumb">
      <el-breadcrumb-item to="/home">首页</el-breadcrumb-item>
      <el-breadcrumb-item>用户管理</el-breadcrumb-item>
      <el-breadcrumb-item>用户列表</el-breadcrumb-item>
    </el-breadcrumb>

    <el-card shadow="never" class="toolbar-card">
      <el-row :gutter="10" class="toolbar">
        <el-col :span="8">
          <el-input
            v-model="searchName"
            placeholder="请输入用户名"
            clearable
            @clear="search"
          >
            <el-button
              slot="append"
              icon="el-icon-search"
              @click="search"
            />
          </el-input>
        </el-col>

        <el-col :span="8" class="toolbar-buttons">
          <el-button
            type="primary"
            icon="el-icon-circle-plus-outline"
            @click="openAdd"
          >
            新增用户
          </el-button>

          <el-button
            type="danger"
            icon="el-icon-delete"
            plain
            @click="batchDelete"
          >
            批量删除
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" class="table-card">
      <el-table
        v-loading="tableLoading"
        :data="tableData"
        border
        class="user-table"
        highlight-current-row
        empty-text="暂无用户数据"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="id" label="用户ID" width="80" />
        <el-table-column prop="name" label="用户名" />
        <el-table-column prop="type_name" label="用户类型" width="120" />
        <el-table-column prop="device_list_str" label="关联设备" min-width="200">
          <template slot-scope="scope">
            <span v-if="scope.row.device_list && scope.row.device_list.length">
              {{ scope.row.device_list.join(', ') }}
            </span>
            <span v-else class="text-muted">暂无</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template slot-scope="scope">
            <el-button type="text" @click="openEdit(scope.row)">编辑</el-button>
            <el-button type="text" class="danger-text" @click="deleteUser(scope.row)">删除</el-button>
            <el-button type="text" @click="openResetPwd(scope.row)">重置密码</el-button>
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

    <el-dialog
      :title="isEdit ? '编辑用户' : '新增用户'"
      :visible.sync="dialogVisible"
      width="460px"
      @close="resetForm"
    >
      <el-form
        ref="userForm"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="name">
          <el-input v-model="form.name" :disabled="isEdit" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码，不少于6位" show-password />
        </el-form-item>

        <el-form-item label="用户类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择用户类型" style="width:100%">
            <el-option label="超级管理员" :value="1" />
            <el-option label="客户" :value="2" />
          </el-select>
        </el-form-item>

        <el-form-item label="关联设备" prop="device_list">
          <el-button type="primary" plain icon="el-icon-s-platform" @click="openDeviceSelect">
            {{ deviceListDisplay || '点击选择设备' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
      </div>
    </el-dialog>

    <el-dialog
      title="选择关联设备"
      :visible.sync="deviceSelectVisible"
      width="600px"
      @close="closeDeviceSelect"
    >
      <el-input
        v-model="deviceSearchKeyword"
        placeholder="输入设备名称或设备ID搜索"
        clearable
        prefix-icon="el-icon-search"
        style="margin-bottom: 12px"
        @clear="searchDeviceList"
        @keyup.enter.native="searchDeviceList"
        @input="searchDeviceList"
      />
      <el-table
        ref="deviceTable"
        :data="filteredDeviceList"
        border
        height="320"
        row-key="device_id"
        @selection-change="handleDeviceSelectionChange"
      >
        <el-table-column type="selection" width="55" :reserve-selection="true" />
        <el-table-column prop="device_id" label="设备ID" width="140" />
        <el-table-column prop="device_name" label="设备名称" />
      </el-table>
      <div slot="footer" class="dialog-footer">
        <el-button @click="deviceSelectVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmDeviceSelect">确定</el-button>
      </div>
    </el-dialog>

    <el-dialog
      title="重置密码"
      :visible.sync="resetPwdDialogVisible"
      width="420px"
      @close="resetResetPwdForm"
    >
      <el-form
        ref="resetPwdForm"
        :model="resetPwdForm"
        :rules="resetPwdRules"
        label-width="90px"
      >
        <el-form-item label="新密码" prop="new_pwd">
          <el-input v-model="resetPwdForm.new_pwd" type="password" placeholder="不少于6位" show-password />
        </el-form-item>
      </el-form>

      <div slot="footer" class="dialog-footer">
        <el-button @click="resetPwdDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitResetPwd">确定</el-button>
      </div>
    </el-dialog>

  </div>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
export default {
  data () {
    return {
      tableData: [],
      tableLoading: false,
      selectedRows: [],
      total: 0,
      page: 1,
      pageSize: 10,
      searchName: '',
      dialogVisible: false,
      resetPwdDialogVisible: false,
      deviceSelectVisible: false,
      isEdit: false,
      form: {},
      resetPwdForm: {},
      allDeviceList: [],
      filteredDeviceList: [],
      deviceSearchKeyword: '',
      selectedDevices: [],

      rules: {
        name: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码不能少于6位', trigger: 'blur' }
        ],
        type: [
          { required: true, message: '请选择用户类型', trigger: 'change' }
        ]
      },
      resetPwdRules: {
        new_pwd: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { min: 6, message: '密码不能少于6位', trigger: 'blur' }
        ]
      }
    }
  },

  computed: {
    deviceListDisplay () {
      const ids = (this.form.device_list || []).length
      return ids ? `已选 ${ids} 个设备` : ''
    }
  },

  created () {
    this.getTableData()
  },

  methods: {
    async getTableData () {
      this.tableLoading = true
      try {
        const { data: res } = await this.$axios.get('/user/user_list/', {
          params: {
            page: this.page,
            page_size: this.pageSize,
            name: this.searchName
          }
        })
        if (res.code === 200) {
          this.tableData = res.data.user_list
          this.total = res.data.total
        } else {
          this.$message.error(res.msg || '获取列表失败')
        }
      } finally {
        this.tableLoading = false
      }
    },

    search () {
      this.page = 1
      this.getTableData()
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

    handleSelectionChange (rows) {
      this.selectedRows = rows
    },

    openAdd () {
      this.isEdit = false
      this.form = {
        name: '',
        password: '',
        type: 2,
        device_list: []
      }
      this.dialogVisible = true
    },

    openEdit (row) {
      this.isEdit = true
      this.form = {
        id: row.id,
        name: row.name,
        type: row.type,
        device_list: [...(row.device_list || [])]
      }
      this.dialogVisible = true
    },

    async openDeviceSelect () {
      this.deviceSearchKeyword = ''
      const { data: res } = await this.$axios.get('/device/simple_list/')
      if (res.code === 200) {
        this.allDeviceList = res.data.device_list || []
        this.filteredDeviceList = [...this.allDeviceList]
        this.selectedDevices = []
        this.deviceSelectVisible = true
        this.$nextTick(() => {
          if (this.$refs.deviceTable && this.form.device_list && this.form.device_list.length) {
            this.filteredDeviceList.forEach(row => {
              if (this.form.device_list.includes(row.device_id)) {
                this.$refs.deviceTable.toggleRowSelection(row, true)
              }
            })
          }
        })
      }
    },

    searchDeviceList () {
      const kw = (this.deviceSearchKeyword || '').trim().toLowerCase()
      if (!kw) {
        this.filteredDeviceList = [...this.allDeviceList]
      } else {
        this.filteredDeviceList = this.allDeviceList.filter(d =>
          (d.device_id || '').toLowerCase().includes(kw) ||
          (d.device_name || '').toLowerCase().includes(kw)
        )
      }
    },

    handleDeviceSelectionChange (rows) {
      this.selectedDevices = rows
    },

    confirmDeviceSelect () {
      this.form.device_list = (this.selectedDevices || []).map(d => d.device_id)
      this.deviceSelectVisible = false
    },

    closeDeviceSelect () {
      this.deviceSearchKeyword = ''
      this.allDeviceList = []
      this.filteredDeviceList = []
      this.selectedDevices = []
    },

    resetForm () {
      this.$refs.userForm && this.$refs.userForm.resetFields()
      this.form = {}
      this.isEdit = false
    },

    submit () {
      this.$refs.userForm.validate(async valid => {
        if (!valid) return

        const payload = {
          name: this.form.name,
          type: this.form.type,
          device_list: (this.form.device_list || []).join(',')
        }
        if (!this.isEdit) {
          payload.password = this.form.password
        }
        if (this.isEdit) {
          payload.id = this.form.id
        }

        const api = this.isEdit
          ? this.$axios.put('/user/register/', this.$qs.stringify(payload))
          : this.$axios.post('/user/register/', this.$qs.stringify(payload))

        const { data: res } = await api
        if (res.code === 200) {
          this.$message.success('操作成功')
          this.dialogVisible = false
          this.getTableData()
        } else {
          this.$message.error(res.msg || '操作失败')
        }
      })
    },

    async deleteUser (row) {
      await this.$confirm(`确认删除用户「${row.name}」吗？该操作不可撤销。`, '删除确认', { type: 'warning' })

      const { data: res } = await this.$axios.delete('/user/register/', {
        params: { id: row.id }
      })

      if (res.code === 200) {
        this.$message.success('删除成功')
        this.getTableData()
      } else {
        this.$message.error(res.msg || '删除失败')
      }
    },

    async batchDelete () {
      if (!this.selectedRows.length) {
        this.$message.warning('请先选择要删除的用户')
        return
      }

      await this.$confirm(
        `确认删除选中的 ${this.selectedRows.length} 个用户吗？该操作不可撤销。`,
        '批量删除确认',
        { type: 'warning' }
      )

      const ids = this.selectedRows.map(r => r.id)
      const { data: res } = await this.$axios.post('/user/batch_delete/', { ids }, {
        headers: { 'Content-Type': 'application/json' }
      })

      if (res.code === 200) {
        this.$message.success('批量删除成功')
        this.getTableData()
      } else {
        this.$message.error(res.msg || '批量删除失败')
      }
    },

    openResetPwd (row) {
      this.resetPwdForm = { id: row.id, new_pwd: '' }
      this.resetPwdDialogVisible = true
    },

    resetResetPwdForm () {
      this.$refs.resetPwdForm && this.$refs.resetPwdForm.resetFields()
      this.resetPwdForm = {}
      this.resetPwdDialogVisible = false
    },

    submitResetPwd () {
      this.$refs.resetPwdForm.validate(async valid => {
        if (!valid) return
        const { data: res } = await this.$axios.put('/user/reset_password/', this.$qs.stringify(this.resetPwdForm), {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })

        if (res.code === 200) {
          this.$message.success('重置密码成功')
          this.resetResetPwdForm()
        } else {
          this.$message.error(res.msg || '重置密码失败')
        }
      })
    }
  }
}
</script>

<style scoped>
.user-page {
  background: #f1f5f9;
  padding: 18px;
  min-height: calc(100vh - 120px);
  font-size: 14px;
  color: #334155;
}

.breadcrumb {
  margin-bottom: 14px;
}

.toolbar-card {
  margin-bottom: 12px;
}

.toolbar {
  margin-bottom: 0;
  display: flex;
  align-items: center;
}

.toolbar-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.table-card {
  margin-bottom: 12px;
}

.user-table ::v-deep th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
}

.user-table ::v-deep td {
  background: #fff;
  color: #334155;
}

.user-table ::v-deep tr:hover td {
  background: #f8fbff;
}

.danger-text {
  color: #f56c6c;
}

.text-muted {
  color: #94a3b8;
}

.pagination {
  margin-top: 16px;
  text-align: right;
}

.dialog-footer {
  text-align: right;
}
</style>
