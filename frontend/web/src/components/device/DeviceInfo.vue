<template>
  <div class="device-page">

    <el-breadcrumb separator-class="el-icon-arrow-right" class="breadcrumb">
      <el-breadcrumb-item to="/home">首页</el-breadcrumb-item>
      <el-breadcrumb-item>设备管理</el-breadcrumb-item>
      <el-breadcrumb-item>设备列表</el-breadcrumb-item>
    </el-breadcrumb>

    <el-row :gutter="10" class="toolbar">
      <el-col :span="8">
        <el-input v-model="searchName" placeholder="设备名称" clearable @clear="search">
          <el-button slot="append" icon="el-icon-search" @click="search" />
        </el-input>
      </el-col>
      <el-col :span="8">
        <el-input v-model="searchDeviceId" placeholder="设备ID" clearable @clear="search">
          <el-button slot="append" icon="el-icon-search" @click="search" />
        </el-input>
      </el-col>
      <el-col :span="8" class="toolbar-buttons">
        <el-button type="primary" icon="el-icon-plus" @click="openAdd">新增设备</el-button>
        <el-button type="danger" icon="el-icon-delete" plain @click="batchDelete">批量删除</el-button>
      </el-col>
    </el-row>

    <el-table :data="tableData" border class="device-table" highlight-current-row @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="device_id" label="设备ID" width="140" />
      <el-table-column prop="device_name" label="设备名称" min-width="160" />
      <el-table-column prop="status_name" label="状态" width="90">
        <template slot-scope="scope">
          <el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">
            {{ scope.row.status_name }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" min-width="160" />
      <el-table-column prop="create_time" label="创建时间" width="180" />
      <el-table-column label="操作" width="140" fixed="right">
        <template slot-scope="scope">
          <el-button type="text" @click="openEdit(scope.row)">编辑</el-button>
          <el-button type="text" class="danger-text" @click="deleteDevice(scope.row)">删除</el-button>
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

    <el-dialog :title="isEdit ? '编辑设备' : '新增设备'" :visible.sync="dialogVisible" width="460px" @close="resetForm">
      <el-form ref="deviceForm" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="设备ID" prop="device_id">
          <el-input v-model="form.device_id" :disabled="isEdit" placeholder="如 device_001" />
        </el-form-item>
        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="form.device_name" placeholder="设备名称" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="备注信息" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
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
      selectedRows: [],
      total: 0,
      page: 1,
      pageSize: 10,
      searchName: '',
      searchDeviceId: '',
      dialogVisible: false,
      isEdit: false,
      form: {},
      rules: {
        device_id: [{ required: true, message: '请输入设备ID', trigger: 'blur' }],
        device_name: [{ required: true, message: '请输入设备名称', trigger: 'blur' }]
      }
    }
  },
  created () {
    this.getTableData()
  },
  methods: {
    async getTableData () {
      const { data: res } = await this.$axios.get('/device/list/', {
        params: { page: this.page, page_size: this.pageSize, name: this.searchName, device_id: this.searchDeviceId }
      })
      if (res.code === 200) {
        this.tableData = res.data.device_list
        this.total = res.data.total
      } else {
        this.$message.error(res.msg || '获取列表失败')
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
      this.form = { device_id: '', device_name: '', remark: '' }
      this.dialogVisible = true
    },
    openEdit (row) {
      this.isEdit = true
      this.form = { id: row.id, device_id: row.device_id, device_name: row.device_name, remark: row.remark || '' }
      this.dialogVisible = true
    },
    resetForm () {
      this.$refs.deviceForm && this.$refs.deviceForm.resetFields()
      this.form = {}
      this.isEdit = false
    },
    submit () {
      this.$refs.deviceForm.validate(async valid => {
        if (!valid) return
        const payload = { device_id: this.form.device_id, device_name: this.form.device_name, remark: this.form.remark || '' }
        const api = this.isEdit
          ? this.$axios.put('/device/detail/', this.$qs.stringify({ ...payload, id: this.form.id }))
          : this.$axios.post('/device/detail/', this.$qs.stringify(payload))
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
    async deleteDevice (row) {
      await this.$confirm(`确认删除设备 ${row.device_name}？`, '提示', { type: 'warning' })
      const { data: res } = await this.$axios.delete('/device/detail/', { params: { id: row.id } })
      if (res.code === 200) {
        this.$message.success('删除成功')
        this.getTableData()
      } else {
        this.$message.error(res.msg || '删除失败')
      }
    },
    async batchDelete () {
      if (!this.selectedRows.length) {
        this.$message.warning('请选择要删除的设备')
        return
      }
      await this.$confirm(`确认删除选中的 ${this.selectedRows.length} 个设备？`, '批量删除', { type: 'warning' })
      const ids = this.selectedRows.map(r => r.id)
      const { data: res } = await this.$axios.post('/device/batch_delete/', { ids }, { headers: { 'Content-Type': 'application/json' } })
      if (res.code === 200) {
        this.$message.success('批量删除成功')
        this.getTableData()
      } else {
        this.$message.error(res.msg || '批量删除失败')
      }
    }
  }
}
</script>

<style scoped>
.device-page { padding: 20px; min-height: 100vh; font-size: 14px; }
.breadcrumb { margin-bottom: 20px; }
.toolbar { margin-bottom: 10px; display: flex; align-items: center; }
.toolbar-buttons { display: flex; gap: 10px; }
.device-table ::v-deep th { background: #fff; color: #606266; }
.device-table ::v-deep td { background: #fff; color: #333; }
.device-table ::v-deep tr:hover { background: #f5f7fa; }
.danger-text { color: #f56c6c; }
.pagination { margin-top: 20px; }
.dialog-footer { text-align: right; }
</style>
