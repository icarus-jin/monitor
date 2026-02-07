<template>
  <div class="login-container">
    <div class="login-box">
        <div class="login-logo">
            <img src="../assets/logo.png" alt="">
        </div>
        <div class="login-form">
            <el-form ref="userRef" :model="userForm" :rules="userRules">
                <el-form-item prop="username">
                    <el-input v-model="userForm.username" placeholder="用户名" prefix-icon="el-icon-user"></el-input>
                </el-form-item>
                <el-form-item prop="password">
                    <el-input v-model="userForm.password" placeholder="密码" prefix-icon="el-icon-lock" show-password></el-input>
                </el-form-item>
                <el-form-item>
                    <el-row :gutter="12">
                    <el-col :span="8">
                        <el-button style="width:100%">注册</el-button>
                    </el-col>
                    <el-col :span="8">
                        <el-button @click="login" type="primary" style="width:100%">登录</el-button>
                    </el-col>
                    <el-col :span="8">
                        <el-button @click="restForm" style="width:100%">重置</el-button>
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
          { required: true, message: '请输入用户名', trigger: ['blur', 'change'] }, // 也可以加入pattern属性，自定义正则表达式
          { min: 5, max: 10, message: '长度在 5 到 10 个字符', trigger: ['blur', 'change'] }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: ['blur', 'change'] }
        ]
      }
    }
  },
  methods: {
    restForm () {
      console.log('重置表单')
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

<!-- less模式，所以下面的.login-logo里面可以去定义img的样式，写外面也可以 -->
<style lang="less" scoped>
.login-container {
  height: 100%;
//   background-image: url('../assets/bg.png');
  background-size: cover;
  background-color: #020617;
}

.login-box {
  width: 350px;
  height: 350px;
  background-color: #fff;
  border-radius: 10px;
  padding: 20px;
  position: relative;
  left: 80%;
  top: 50%;
  transform: translate(-50%, -50%);
}

.login-logo {
  height: 100px;
  width: 100px;
  border: 1px solid #eee;
  padding: 10px;
  border-radius: 10%;
  position: absolute;
  left: 50%;
  top: 20px;
  transform: translateX(-50%);
  box-shadow: 0 0 10px #ccc;
  img {
    height: 100%;
    width: 100%;
  }
}

.login-form {
  position: absolute;
  top: 160px;
  left: 40px;
  right: 40px;
  padding-top: 20px;
  box-sizing: border-box;
}
</style>
