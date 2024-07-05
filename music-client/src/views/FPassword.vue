<template>
    <yin-login-logo></yin-login-logo>
    <div class="sign">
      <div class="sign-head">
      <h1>修改密码</h1></div>
    <el-main>
      <el-form v-model="emailForm"  ref="emailForm" :model="emailForm" @submit.prevent="sendVerificationCode" :rules="SendEmailRules">
        <el-form-item label="邮箱：" prop="email">
          <el-input id="email" v-model="emailForm.email" type="email"/>
          <el-button @click="sendVerificationCode">发送验证码</el-button>
        </el-form-item>
      </el-form>

      <el-form v-model="fPasswordForm" ref="fPasswordForm" :model="fPasswordForm" @submit.prevent="handleSubmit" :rules="ResetPasswordRules">
        <el-form-item label="验证码：" prop="code">
          <el-input id="code" v-model="fPasswordForm.code" type="text"/>
        </el-form-item>
        <el-form-item label="新密码：" prop="password">
          <el-input id="password" v-model="fPasswordForm.password" type="password"/>
        </el-form-item>
        <el-form-item label="确认密码：" prop="confirmPassword">
          <el-input id="confirmPassword" v-model="fPasswordForm.confirmPassword" type="password"/>
        </el-form-item>
        <el-form-item >
          <el-button @click="handleSubmit">提交</el-button>
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
</style>