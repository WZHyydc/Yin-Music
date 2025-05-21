<template>
  <yin-login-logo />
  <div class="sign">
    <div class="sign-head">
      <h1>修改密码</h1>
    </div>
    <el-main>
      <!-- 邮箱验证码表单 -->
      <el-form
        ref="emailForm"
        :model="emailForm"
        :rules="SendEmailRules"
        label-width="100px"
        class="email-form"
        @submit.prevent="sendVerificationCode"
      >
        <el-form-item label="邮箱：" prop="email" class="email-item">
          <div class="email-input-wrapper">
            <el-input
              id="email"
              v-model="emailForm.email"
              type="email"
              placeholder="请输入邮箱"
              class="email-input"
            />
            <el-button
              type="primary"
              @click="sendVerificationCode"
              class="code-btn"
            >
              发送验证码
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <!-- 密码重设表单 -->
      <el-form
        ref="fPasswordForm"
        :model="fPasswordForm"
        :rules="ResetPasswordRules"
        label-width="100px"
        class="password-form"
        @submit.prevent="handleSubmit"
      >
        <el-form-item label="验证码：" prop="code">
          <el-input
            v-model="fPasswordForm.code"
            type="text"
            placeholder="请输入验证码"
          />
        </el-form-item>
        <el-form-item label="新密码：" prop="password">
          <el-input
            v-model="fPasswordForm.password"
            type="password"
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认密码：" prop="confirmPassword">
          <el-input
            v-model="fPasswordForm.confirmPassword"
            type="password"
            placeholder="请确认新密码"
          />
        </el-form-item>
        <el-form-item class="submit-item">
          <el-button
            type="primary"
            native-type="submit"
            class="submit-button"
          >
            提交
          </el-button>
        </el-form-item>
      </el-form>
    </el-main>
  </div>
</template>

<script>
import { HttpManager} from '@/api';
import {SendEmailRules ,ResetPasswordRules } from '@/enums';
import YinLoginLogo from "@/components/layouts/YinLoginLogo.vue";
export default {
  components: {
    YinLoginLogo,
  },
  data() {
    return {
      emailForm: {
        email: "",
      },
      fPasswordForm:{
        code: "",
        password: "",
        confirmPassword: "", 
      },
      SendEmailRules,
      ResetPasswordRules,
    };
  },
  methods: {
    async sendVerificationCode() {
      let canRun = true;

      this.$refs["emailForm"].validate((valid) => {
        if (!valid) return (canRun = false);
      });
      if (!canRun) {return;}

      try {
        const email =document.getElementById('email').value;
        console.log(email);
        const response = await HttpManager.sendVerificationCode(email);
        console.log(response.type);
        console.log(response);
        this.$message({
          message: response.message,
          type: response.type
        });
      } catch (error) {
        console.error('Error submitting email:');
        this.$message({
        message: 'Error submitting email:',
        type: 'error'
      });
 } 
   },
  async handleSubmit() {

  let canRun = true;
    this.$refs["emailForm"].validate((valid) => {
      if (!valid){return;}
    });
  if (!canRun) return;
  let canRun2 = true;
  this.$refs["fPasswordForm"].validate((valid) => {
    if (!valid) return (canRun2 = false);
  });
  if (!canRun2) return;

  try {
    const email =document.getElementById('email').value;
    const code=document.getElementById('code').value
    console.log(code);
    const password=document.getElementById('password').value
    const confirmPassword=document.getElementById('confirmPassword').value
    const data = {
      email: email,
      code: code,
      password: password,
      confirmPassword: confirmPassword
    };
    const response = await HttpManager.resetPassword(data);
    console.log(response);
    this.$message({
      message: response.message,
      type: response.type
    });
  } catch (error) {
    this.$message({
      message: 'response.data',
      type: 'error'
    });
  }
}

},
};
</script>

<style lang="scss" scoped>
@import "@/assets/css/sign.scss";

/* 防止标签文字换行 */
.el-form-item__label {
  white-space: nowrap;
}

.email-form .email-item {
  margin-bottom: 20px;
}

.email-form .email-input {
  width: 100%;
  min-width: 0;
}

.email-form .email-input-wrapper {
  display: flex;
  flex-direction: column;
}

.email-form .code-btn {
  margin-top: 10px;
  align-self: flex-start;
}

.password-form .el-form-item {
  margin-bottom: 20px;
}

.submit-item {
  text-align: center;
  margin-top: 20px;

  .submit-button {
    width: 200px;
  }
}
</style>