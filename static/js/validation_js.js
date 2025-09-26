// Forms
let pmessage = document.getElementById("id_p");
let changeform = document.getElementById("changeform");
let loginform = document.getElementById("custom-loginform");
let resetform = document.getElementById("resetForm");
let sendemailform = document.getElementById("sendemailForm");
let signupform = document.getElementById("signupForm");
let contactform = document.getElementById("contactForm");
let my_accountform = document.getElementById("myaccountForm");
let variationform = document.getElementById("variationForm");
let addressform = document.getElementById("addressForm");
let UnCompleteOrdersForm = document.getElementById("UnCompleteOrdersForm");
let CheckoutShippingBillingForm = document.getElementById("checkout_shipping_billingForm");

// Address Infomation
let shipping_first_name = document.querySelector("[name='shipping-first_name']");
let shipping_last_name = document.querySelector("[name='shipping-last_name']");
let shipping_email = document.querySelector("[name='shipping-email']");
let shipping_phone = document.querySelector("[name='shipping-phone']");
let shipping_address1 = document.querySelector("[name='shipping-address1']");
let shipping_city = document.querySelector("[name='shipping-city']");
let billing_first_name = document.querySelector("[name='billing-first_name']");
let billing_last_name = document.querySelector("[name='billing-last_name']");
let billing_email = document.querySelector("[name='billing-email']");
let billing_phone = document.querySelector("[name='billing-phone']");
let billing_address1 = document.querySelector("[name='billing-address1']");
let billing_city = document.querySelector("[name='billing-city']");

// Checkout
let checkout_shipping_first_name = document.querySelector("[name='shipping_first_name']");
let checkout_shipping_last_name = document.querySelector("[name='shipping_last_name']");
let checkout_shipping_email = document.querySelector("[name='shipping_email']");
let checkout_shipping_phone = document.querySelector("[name='shipping_phone']");
let checkout_shipping_address1 = document.querySelector("[name='shipping_address1']");
let checkout_shipping_city = document.querySelector("[name='shipping_city']");
let checkout_billing_first_name = document.querySelector("[name='billing_first_name']");
let checkout_billing_last_name = document.querySelector("[name='billing_last_name']");
let checkout_billing_email = document.querySelector("[name='billing_email']");
let checkout_billing_phone = document.querySelector("[name='billing_phone']");
let checkout_billing_address1 = document.querySelector("[name='billing_address1']");
let checkout_billing_city = document.querySelector("[name='billing_city']");
let payment_optionfield = document.querySelectorAll("[name='payment_option']");
const useDefaultShipping = document.querySelector('[name="use_default_shipping"]');
const useDefaultbilling = document.querySelector("[name='use_default_billing']");

// Authentication
let messagefield = document.querySelector("[name='mesasge']");
let loginfield = document.querySelector("[name='login']");
let passwordfield = document.querySelector("[name='password']");
let usernamefield = document.querySelector("[name='username']");
let emailfield = document.querySelector("[name='email']");
let password1field = document.querySelector("[name='password1']");
let password2field = document.querySelector("[name='password2']");
let oldpasswordfield = document.querySelector("[name='oldpassword']");

if (UnCompleteOrdersForm) {
  UnCompleteOrdersForm.onsubmit = function (e) {
    if (payment_optionfield[0].checked === false && payment_optionfield[1].checked === false) {
      pmessage.innerHTML = "You Must To Select One Of This Fields";
      e.preventDefault();
    }
  };
}

if (loginform) {
  loginform.onsubmit = function (e) {
    if (loginfield.value === "" || passwordfield.value === "") {
      pmessage.innerHTML = "all Fields are Required";
      e.preventDefault();
    }
  };
}

if (changeform) {
  changeform.onsubmit = function (e) {
    if (
      password1field.value === "" ||
      password2field.value === "" ||
      oldpasswordfield.value === ""
    ) {
      pmessage.innerHTML = "all Fields are Required";
      e.preventDefault();
    }
  };
}

if (resetform) {
  resetform.onsubmit = function (e) {
    if (password1field.value === "" || password2field.value === "") {
      pmessage.innerHTML = "all Fields are Required";
      e.preventDefault();
    }
  };
}

if (sendemailform) {
  sendemailform.onsubmit = function (e) {
    if (emailfield.value === "") {
      pmessage.innerHTML = "This Field is Required";
      e.preventDefault();
    }
  };
}

if (signupform) {
  signupform.onsubmit = function (e) {
    if (
      usernamefield.value === "" ||
      emailfield.value === "" ||
      password1field.value === "" ||
      password2field.value === ""
    ) {
      pmessage.innerHTML = "all Fields are Required";
      e.preventDefault();
    }
  };
}

if (contactform) {
  contactform.onsubmit = function (e) {
    if (emailfield.value === "" || messagefield.value === "") {
      pmessage.innerHTML = "All Fields are Required";
      e.preventDefault();
    }
  };
}

if (my_accountform) {
  my_accountform.onsubmit = function (e) {
    if (usernamefield.value === "") {
      pmessage.innerHTML = "Username Field is Required";
      e.preventDefault();
    }
  };
}

if (addressform) {
  addressform.onsubmit = function (e) {
    if (
      shipping_first_name.value === "" ||
      shipping_last_name.value === "" ||
      shipping_email.value === "" ||
      shipping_phone.value === "" ||
      shipping_address1.value === "" ||
      shipping_city.value === "" ||
      billing_first_name.value === "" ||
      billing_last_name.value === "" ||
      billing_email.value === "" ||
      billing_phone.value === "" ||
      billing_address1.value === "" ||
      billing_city.value === ""
    ) {
      pmessage.innerHTML = "Fill in The Asterisk Fields";
      e.preventDefault();
    }
  };
}

if (CheckoutShippingBillingForm) {
  CheckoutShippingBillingForm.onsubmit = function (e) {
    if (useDefaultShipping.checked === false && useDefaultbilling.checked === false ) {
      if (
        payment_optionfield[0].checked === false && payment_optionfield[1].checked === false ||
        checkout_shipping_first_name.value === "" ||
        checkout_shipping_last_name.value === "" ||
        checkout_shipping_email.value === "" ||
        checkout_shipping_phone.value === "" ||
        checkout_shipping_address1.value === "" ||
        checkout_shipping_city.value === "" ||
        checkout_billing_first_name.value === "" ||
        checkout_billing_last_name.value === "" ||
        checkout_billing_email.value === "" ||
        checkout_billing_phone.value === "" ||
        checkout_billing_address1.value === "" ||
        checkout_billing_city.value === "" 
      ) {
        pmessage.innerHTML = "Fill in The Required Fields";
        e.preventDefault();
      }
    } else {
      if (payment_optionfield[0].checked === false && payment_optionfield[1].checked === false ) {
        pmessage.innerHTML = "Fill in The Required Fields from else";
        e.preventDefault();
      }
    }
  };
}
