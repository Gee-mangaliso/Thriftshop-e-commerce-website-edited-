
// Replace the mock register function
//window.register = async function register() {
//    console.log("REGISTER FUNCTION CALLED");
//
//    const name = document.getElementById('registerName').value;
//    const email = document.getElementById('registerEmail').value;
//    const password = document.getElementById('registerPassword').value;
//    const confirmPassword = document.getElementById('registerConfirmPassword').value;
//    const phone = document.getElementById('registerPhone').value;
//
//    if (!name || !email || !password || !confirmPassword) {
//        showAlert('Please fill in all fields', 'error');
//        return;
//    }
//
//    if (password !== confirmPassword) {
//        showAlert('Passwords do not match', 'error');
//        return;
//    }
//
//    try {
//        const userData = {
//            full_name: name,
//            email: email,
//            password: password,
//            phone: SAUtils.formatPhone(phone)
//        };
//
//        const result = await api.register(userData);
//
//        if (result.user) {
//        state.currentUser = result.user;
//        localStorage.setItem('currentUser', JSON.stringify(result.user));
//        } else {
//         console.warn("No user object returned from backend:", result);
//        }
//
//        updateAuthUI();
//        showAlert('Registration successful!', 'success');
//        showPage('home');
//
//    } catch (error) {
//        handleApiError(error);
//    }
//}
