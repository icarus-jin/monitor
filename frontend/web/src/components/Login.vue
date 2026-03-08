<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-logo">
        <img src="../assets/logo.png" alt="logo">
      </div>
      <div class="login-title">欢迎登录</div>
      <div class="login-subtitle">气象监测管理系统</div>

      <div class="login-form">
        <el-form ref="userRef" :model="userForm" :rules="userRules">
          <el-form-item prop="username">
            <el-input v-model="userForm.username" placeholder="用户名" prefix-icon="el-icon-user"></el-input>
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="userForm.password" placeholder="密码" prefix-icon="el-icon-lock" show-password></el-input>
          </el-form-item>
          <el-form-item>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-button @click="resetForm" style="width:100%">重置</el-button>
              </el-col>
              <el-col :span="12">
                <el-button @click="login" type="primary" style="width:100%">登录</el-button>
              </el-col>
            </el-row>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint vue/multi-word-component-names: "off" */
export default {
  data () {
    return {
      userForm: {
        username: '',
        password: ''
      },
      userRules: {
        username: [
          { required: true, message: '请输入用户名', trigger: ['blur', 'change'] },
          { min: 5, max: 20, message: '长度在 5 到 20 个字符', trigger: ['blur', 'change'] }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: ['blur', 'change'] }
        ]
      }
    }
  },
  methods: {
    resetForm () {
      this.$refs.userRef.resetFields()
    },
    login () {
      this.$refs.userRef.validate(valid => {
        if (!valid) return

        this.$axios.post('/user/login/', this.$qs.stringify(this.userForm))
          .then(({ data: res }) => {
            if (res.code !== 200) {
              this.$message.error(res.msg)
              return
            }

            window.sessionStorage.setItem('token', res.data.token)
            window.sessionStorage.setItem('username', res.data.username)
            window.sessionStorage.setItem('user_type', String(res.data.user_type || ''))
            this.$message.success(res.msg)
            this.$router.push('/home')
          })
          .catch(() => {
            this.$message.error('网络异常')
          })
      })
    }
  }
}
</script>

<style lang="less" scoped>
.login-container {
  height: 100%;
  background: linear-gradient(135deg, #eef2ff 0%, #e2e8f0 100%);
}

.login-box {
  width: 380px;
  height: 400px;
  background-color: #fff;
  border-radius: 14px;
  padding: 20px 26px;
  position: relative;
  left: 78%;
  top: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 16px 38px rgba(15, 23, 42, 0.14);
  border: 1px solid #e2e8f0;
}

.login-logo {
  height: 88px;
  width: 88px;
  border: 1px solid #e5e7eb;
  padding: 8px;
  border-radius: 12px;
  position: absolute;
  left: 50%;
  top: 20px;
  transform: translateX(-50%);
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.1);
  background: #fff;

  img {
    height: 100%;
    width: 100%;
  }
}

.login-title {
  margin-top: 118px;
  text-align: center;
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
}

.login-subtitle {
  margin-top: 6px;
  text-align: center;
  font-size: 13px;
  color: #64748b;
}

.login-form {
  margin-top: 22px;
}
</style>
