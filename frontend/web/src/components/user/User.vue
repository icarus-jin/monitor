<template>
  <div class="user-page">

    <!-- 面包屑 -->
    <el-breadcrumb separator-class="el-icon-arrow-right" class="breadcrumb">
      <el-breadcrumb-item to="/home">首页</el-breadcrumb-item>
      <el-breadcrumb-item>用户管理</el-breadcrumb-item>
      <el-breadcrumb-item>用户列表</el-breadcrumb-item>
    </el-breadcrumb>

    <!-- 工具栏 -->
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

    <!-- 用户表格 -->
    <el-table
      :data="tableData"
      border
      class="user-table"
      style="margin-top: 20px"
      highlight-current-row
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />

      <el-table-column prop="id" label="用户ID" />
      <el-table-column prop="name" label="用户名" />
      <el-table-column prop="nick_name" label="昵称" />
      <el-table-column prop="phone" label="电话" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="role_name" label="角色" />

      <el-table-column label="操作" width="180">
        <template slot-scope="scope">
          <el-button type="text" @click="openEdit(scope.row)">编辑</el-button>
          <el-button type="text" class="danger-text" @click="deleteUser(scope.row)">删除</el-button>
          <el-button type="text" @click="openResetPwd(scope.row)">重置密码</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
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

    <!-- 新增 / 编辑弹窗 -->
    <el-dialog
      :title="isEdit ? '编辑用户' : '新增用户'"
      :visible.sync="dialogVisible"
      width="420px"
      @close="resetForm"
    >
      <el-form
        ref="userForm"
        :model="form"
        :rules="rules"
        label-width="90px"
      >
        <el-form-item label="用户名" prop="name">
          <el-input v-model="form.name" :disabled="isEdit" />
        </el-form-item>

        <el-form-item label="昵称" prop="nick_name">
          <el-input v-model="form.nick_name" />
        </el-form-item>

        <el-form-item v-if="!isEdit" label="密码" prop="pwd">
          <el-input type="password" v-model="form.pwd" />
        </el-form-item>

        <el-form-item v-if="!isEdit" label="确认密码" prop="confirm_pwd">
          <el-input type="password" v-model="form.confirm_pwd" />
        </el-form-item>

        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>

        <el-form-item label="角色" prop="role_id">
          <el-select v-model="form.role_id" placeholder="请选择角色">
            <el-option
              v-for="role in roleList"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            >
            <span style="float: left">{{ role.id }}</span>
            <span style="float: left; padding-left: 50px;">{{ role.name }}</span>
            <span style="float: right; color: #8492a6; font-size: 13px; padding-left: 100px; ">{{ role.desc }}</span>
          </el-option>
          </el-select>
        </el-form-item>

      </el-form>

      <div slot="footer" class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submit">确定</el-button>
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
        :model="resetPwdform"
        label-width="90px"
      >
        <el-form-item label="新密码" prop="new_pwd">
          <el-input type="password" v-model="resetPwdform.new_pwd" />
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
      selectedRows: [],
      total: 0,
      page: 1,
      pageSize: 10,
      searchName: '',
      dialogVisible: false,
      resetPwdDialogVisible: false,
      isEdit: false,
      form: {},
      resetPwdform: {},
      roleList: [],

      rules: {
        name: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        nick_name: [
          { required: true, message: '请输入昵称', trigger: 'blur' }
        ],
        pwd: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, message: '密码不能少于6位', trigger: 'blur' }
        ],
        confirm_pwd: [
          { required: true, message: '请确认密码', trigger: 'blur' },
          {
            validator: (rule, value, callback) => {
              if (value !== this.form.pwd) {
                callback(new Error('两次密码不一致'))
              } else {
                callback()
              }
            },
            trigger: 'blur'
          }
        ],
        phone: [
          { required: true, message: '请输入电话', trigger: 'blur' }
        ],
        email: [
          { required: true, message: '请输入邮箱', trigger: 'blur' },
          { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
        ]
      }
    }
  },

  created () {
    this.getTableData()
    this.getRoleList()
  },

  methods: {
    async getTableData () {
      const res = await this.$axios.get('/user/user_list', {
        params: {
          page: this.page,
          page_size: this.pageSize,
          name: this.searchName
        }
      })
      if (res.data.code === 200) {
        this.tableData = res.data.data.user_list
        this.total = res.data.data.total
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
      this.form = {}
      this.dialogVisible = true
    },

    openEdit (row) {
      this.isEdit = true
      this.form = { ...row }
      console.log(this.form)
      this.dialogVisible = true
    },

    resetForm () {
      this.$refs.userForm && this.$refs.userForm.resetFields()
      this.form = {}
      this.isEdit = false
    },

    submit () {
      this.$refs.userForm.validate(async valid => {
        if (!valid) return

        const api = this.isEdit
          ? this.$axios.put('/user/register/', this.$qs.stringify(this.form))
          : this.$axios.post('/user/register/', this.$qs.stringify(this.form))

        const res = await api
        if (res.data.code === 200) {
          this.$message.success('操作成功')
          this.dialogVisible = false
          this.getTableData()
        }
      })
    },

    async deleteUser (row) {
      await this.$confirm(`确认删除用户 ${row.name}？`, '提示', { type: 'warning' })

      const { data: res } = await this.$axios.delete(
        '/user/register/',
        { params: { id: row.id } }
      )

      if (res.code === 200) {
        this.$message.success('删除成功')
        this.getTableData()
      } else {
        this.$message.error(res.msg || '删除失败')
      }
    },

    async batchDelete () {
      if (!this.selectedRows.length) {
        this.$message.warning('请选择要删除的用户')
        return
      }

      await this.$confirm(
        `确认删除选中的 ${this.selectedRows.length} 个用户？`,
        '批量删除',
        { type: 'warning' }
      )

      // 顺序删除，其实要后端提供并发删除接口，然后通过this.selectedRows.map匹配id列表
      for (const row of this.selectedRows) {
        await this.$axios.delete(
          '/user/register/',
          { params: { id: row.id } }
        )
      }

      this.$message.success('批量删除成功')
      this.getTableData()
    },

    openResetPwd (row) {
      console.log(row)
      this.resetPwdform = { id: row.id }
      this.resetPwdDialogVisible = true
    },

    resetResetPwdForm () {
      this.$refs.resetPwdForm && this.$refs.resetPwdForm.resetFields()
      this.resetPwdform = {}
      this.resetPwdDialogVisible = false
    },

    submitResetPwd () {
      this.$refs.resetPwdForm.validate(async valid => {
        if (!valid) return
        console.log(this.resetPwdform)
        const { data: res } = await this.$axios.get(
          '/user/reset_password/',
          { params: this.resetPwdform }
        )

        if (res.code === 200) {
          this.$message.success('重置密码成功')
          this.resetResetPwdForm()
        } else {
          this.$message.error(res.msg || '重置密码失败')
        }
      })
    },

    // 获取角色列表
    async getRoleList () {
      const { data: res } = await this.$axios.get('/role/')
      if (res.code === 200) {
        this.roleList = res.data.role_list
      }
    }

  }
}
</script>

<style scoped>
.user-page {
  background: #f5f6fa;
  padding: 20px;
  min-height: 100vh;
  font-size: 14px;
  color: #333;
}

.breadcrumb {
  margin-bottom: 20px;
}

.toolbar {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.toolbar-buttons {
  display: flex;
  gap: 10px;
}

.user-table ::v-deep th {
  background: #fff;
  color: #606266;
}

.user-table ::v-deep td {
  background: #fff;
  color: #333;
}

.user-table ::v-deep tr:hover {
  background: #e6f7ff;
}

.danger-text {
  color: #f56c6c;
}

.pagination {
  margin-top: 20px;
}

.dialog-footer {
  text-align: right;
}
</style>
