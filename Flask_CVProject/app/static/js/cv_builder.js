// CV Builder JavaScript
let currentCVId = null;
let experiences = [];
let education = [];
let certifications = [];
let projects = [];
let languages = [];

// Tab switching
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.closest('.tab-button').classList.add('active');
}

// Add Experience
function addExperience() {
    const container = document.getElementById('experiencesContainer');
    const index = experiences.length;
    
    const html = `
        <div class="item-card" data-index="${index}">
            <button type="button" class="remove-item-btn" onclick="removeItem('experiences', ${index})">
                <i class="bi bi-x"></i>
            </button>
            <div class="row">
                <div class="col-md-6 form-group">
                    <label class="form-label">Vị trí <span class="text-danger">*</span></label>
                    <input type="text" class="form-control" name="exp_position_${index}" required>
                </div>
                <div class="col-md-6 form-group">
                    <label class="form-label">Công ty <span class="text-danger">*</span></label>
                    <input type="text" class="form-control" name="exp_company_${index}" required>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6 form-group">
                    <label class="form-label">Ngày bắt đầu</label>
                    <input type="month" class="form-control" name="exp_start_${index}">
                </div>
                <div class="col-md-6 form-group">
                    <label class="form-label">Ngày kết thúc</label>
                    <input type="month" class="form-control" name="exp_end_${index}">
                    <div class="form-check mt-2">
                        <input class="form-check-input" type="checkbox" name="exp_current_${index}" onchange="toggleEndDate(${index})">
                        <label class="form-check-label">Hiện tại</label>
                    </div>
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Mô tả công việc</label>
                <textarea class="form-control" name="exp_description_${index}" rows="4"></textarea>
                <button type="button" class="btn btn-sm btn-outline-primary mt-2" onclick="enhanceExperience(${index})">
                    <i class="bi bi-magic me-1"></i>AI Cải thiện
                </button>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    experiences.push({});
}

function toggleEndDate(index) {
    const endDateInput = document.querySelector(`input[name="exp_end_${index}"]`);
    const checkbox = document.querySelector(`input[name="exp_current_${index}"]`);
    endDateInput.disabled = checkbox.checked;
    if (checkbox.checked) {
        endDateInput.value = '';
    }
}

// Add Education
function addEducation() {
    const container = document.getElementById('educationContainer');
    const index = education.length;
    
    const html = `
        <div class="item-card" data-index="${index}">
            <button type="button" class="remove-item-btn" onclick="removeItem('education', ${index})">
                <i class="bi bi-x"></i>
            </button>
            <div class="row">
                <div class="col-md-6 form-group">
                    <label class="form-label">Trường học <span class="text-danger">*</span></label>
                    <input type="text" class="form-control" name="edu_school_${index}" required>
                </div>
                <div class="col-md-6 form-group">
                    <label class="form-label">Chuyên ngành</label>
                    <input type="text" class="form-control" name="edu_major_${index}">
                </div>
            </div>
            <div class="row">
                <div class="col-md-6 form-group">
                    <label class="form-label">Bằng cấp</label>
                    <select class="form-select" name="edu_degree_${index}">
                        <option value="">-- Chọn --</option>
                        <option value="High School">Trung học phổ thông</option>
                        <option value="Associate">Cao đẳng</option>
                        <option value="Bachelor">Đại học</option>
                        <option value="Master">Thạc sĩ</option>
                        <option value="PhD">Tiến sĩ</option>
                    </select>
                </div>
                <div class="col-md-6 form-group">
                    <label class="form-label">Năm tốt nghiệp</label>
                    <input type="number" class="form-control" name="edu_year_${index}" min="1950" max="2030">
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    education.push({});
}

// Add Certification
function addCertification() {
    const container = document.getElementById('certificationsContainer');
    const index = certifications.length;
    
    const html = `
        <div class="item-card" data-index="${index}">
            <button type="button" class="remove-item-btn" onclick="removeItem('certifications', ${index})">
                <i class="bi bi-x"></i>
            </button>
            <div class="row">
                <div class="col-md-6 form-group">
                    <label class="form-label">Tên chứng chỉ</label>
                    <input type="text" class="form-control" name="cert_name_${index}">
                </div>
                <div class="col-md-6 form-group">
                    <label class="form-label">Tổ chức cấp</label>
                    <input type="text" class="form-control" name="cert_org_${index}">
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Ngày cấp</label>
                <input type="month" class="form-control" name="cert_date_${index}">
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    certifications.push({});
}

// Add Project
function addProject() {
    const container = document.getElementById('projectsContainer');
    const index = projects.length;
    
    const html = `
        <div class="item-card" data-index="${index}">
            <button type="button" class="remove-item-btn" onclick="removeItem('projects', ${index})">
                <i class="bi bi-x"></i>
            </button>
            <div class="row">
                <div class="col-md-6 form-group">
                    <label class="form-label">Tên dự án</label>
                    <input type="text" class="form-control" name="proj_name_${index}">
                </div>
                <div class="col-md-6 form-group">
                    <label class="form-label">Link dự án</label>
                    <input type="url" class="form-control" name="proj_url_${index}">
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Mô tả</label>
                <textarea class="form-control" name="proj_description_${index}" rows="3"></textarea>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    projects.push({});
}

// Add Language
function addLanguage() {
    const container = document.getElementById('languagesContainer');
    const index = languages.length;
    
    const html = `
        <div class="item-card" data-index="${index}">
            <button type="button" class="remove-item-btn" onclick="removeItem('languages', ${index})">
                <i class="bi bi-x"></i>
            </button>
            <div class="row">
                <div class="col-md-6 form-group">
                    <label class="form-label">Ngôn ngữ</label>
                    <input type="text" class="form-control" name="lang_name_${index}">
                </div>
                <div class="col-md-6 form-group">
                    <label class="form-label">Trình độ</label>
                    <select class="form-select" name="lang_level_${index}">
                        <option value="">-- Chọn --</option>
                        <option value="Native">Bản ngữ</option>
                        <option value="Fluent">Thành thạo</option>
                        <option value="Advanced">Nâng cao</option>
                        <option value="Intermediate">Trung bình</option>
                        <option value="Basic">Cơ bản</option>
                    </select>
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', html);
    languages.push({});
}

// Remove Item
function removeItem(type, index) {
    const container = document.getElementById(`${type}Container`);
    const item = container.querySelector(`[data-index="${index}"]`);
    if (item) {
        item.remove();
        // Reindex remaining items
        const items = container.querySelectorAll('.item-card');
        items.forEach((item, idx) => {
            item.setAttribute('data-index', idx);
            item.querySelectorAll('input, select, textarea').forEach(input => {
                const name = input.name.replace(/\d+/, idx);
                input.name = name;
            });
        });
        // Remove from array
        if (type === 'experiences') experiences.splice(index, 1);
        else if (type === 'education') education.splice(index, 1);
        else if (type === 'certifications') certifications.splice(index, 1);
        else if (type === 'projects') projects.splice(index, 1);
        else if (type === 'languages') languages.splice(index, 1);
    }
}

// AI Enhance Functions
async function enhanceSummary() {
    const summary = document.getElementById('summaryText').value;
    if (!summary) {
        if (typeof Toast !== 'undefined') {
            Toast.warning('Vui lòng nhập nội dung tóm tắt trước');
        } else {
            alert('Vui lòng nhập nội dung tóm tắt trước');
        }
        return;
    }
    
    showLoading();
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/cv-builder/enhance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                type: 'summary',
                summary: summary
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
  if (data.enhanced) {
    document.getElementById('summaryText').value = data.enhanced;
    if (typeof Toast !== 'undefined') {
        Toast.success('Đã cải thiện nội dung thành công!');
    } else {
        alert('Đã cải thiện nội dung thành công!');
    }
  } else {
    console.warn("AI không trả về nội dung mới:", data);
    if (typeof Toast !== 'undefined') {
        Toast.warning("AI không thể cải thiện nội dung (không có dữ liệu enhanced)");
    } else {
        alert("AI không thể cải thiện nội dung (không có dữ liệu enhanced)");
    }
  }
} else {
  console.warn("AI failed:", data);
  if (typeof Toast !== 'undefined') {
      Toast.error(data.message || "Không thể cải thiện nội dung");
  } else {
      alert(data.message || "Không thể cải thiện nội dung");
  }
}

    } catch (error) {
        console.error('Error:', error);
        if (typeof Toast !== 'undefined') {
            Toast.error('Có lỗi xảy ra khi cải thiện nội dung');
        } else {
            alert('Có lỗi xảy ra khi cải thiện nội dung');
        }
    } finally {
        hideLoading();
    }
}

async function enhanceExperience(index) {
    const position = document.querySelector(`input[name="exp_position_${index}"]`).value;
    const company = document.querySelector(`input[name="exp_company_${index}"]`).value;
    const description = document.querySelector(`textarea[name="exp_description_${index}"]`).value;
    
    if (!position || !company) {
        if (typeof Toast !== 'undefined') {
            Toast.warning('Vui lòng điền vị trí và công ty trước');
        } else {
            if (typeof Toast !== 'undefined') {
                Toast.warning('Vui lòng điền vị trí và công ty trước');
            } else {
                alert('Vui lòng điền vị trí và công ty trước');
            }
        }
        return;
    }
    
    showLoading();
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/cv-builder/enhance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                type: 'experience',
                experience: {
                    position: position,
                    company: company,
                    description: description
                }
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.enhanced) {
            document.querySelector(`textarea[name="exp_description_${index}"]`).value = data.enhanced.description || data.enhanced;
            if (typeof Toast !== 'undefined') {
                Toast.success('Đã cải thiện mô tả công việc thành công!');
            } else {
                alert('Đã cải thiện mô tả công việc thành công!');
            }
        } else {
            if (typeof Toast !== 'undefined') {
                Toast.error('Lỗi: ' + (data.message || 'Không thể cải thiện mô tả'));
            } else {
                alert('Lỗi: ' + (data.message || 'Không thể cải thiện mô tả'));
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (typeof Toast !== 'undefined') {
            Toast.error('Có lỗi xảy ra khi cải thiện mô tả');
        } else {
            alert('Có lỗi xảy ra khi cải thiện mô tả');
        }
    } finally {
        hideLoading();
    }
}

async function exportCV() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        if (typeof Toast !== 'undefined') {
            Toast.warning('Vui lòng đăng nhập để xuất CV');
        } else {
            alert('Vui lòng đăng nhập để xuất CV');
        }
        window.location.href = '/login';
        return;
    }

    // Save form data before export
    saveFormDataToLocalStorage();

    // Sử dụng formData từ preview hoặc collect mới
    const formData = window.previewFormData || collectFormData();
    
    if (!formData.full_name) {
        alert('Vui lòng nhập họ tên');
        return;
    }

    // Hiển thị dialog chọn format
    const format = await showExportFormatDialog();
    if (!format) {
        return; // User cancelled
    }
    
    formData.format = format;

    showLoading();

    try {
        // Upload avatar nếu có file mới và chưa có URL
        const avatarInput = document.getElementById('avatar');
        if (avatarInput && avatarInput.files && avatarInput.files[0] && !formData.avatar_url) {
            const avatarFormData = new FormData();
            avatarFormData.append('avatar', avatarInput.files[0]);
            
            const avatarResponse = await fetch('/api/cv-builder/upload-avatar', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: avatarFormData
            });
            
            if (avatarResponse.ok) {
                const avatarData = await avatarResponse.json();
                if (avatarData.success && avatarData.avatar_url) {
                    formData.avatar_url = avatarData.avatar_url;
                }
            }
        }
        
        const response = await fetch('/api/cv-builder/export-temp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const fileName = `${formData.full_name.replace(/\s+/g, '_')}_CV.${format}`;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
            
            // Show success message
            showToast('Xuất CV thành công!', 'success');
        } else {
            const data = await response.json();
            if (typeof Toast !== 'undefined') {
                Toast.error('Lỗi: ' + (data.message || 'Không thể xuất CV'));
            } else {
                alert('Lỗi: ' + (data.message || 'Không thể xuất CV'));
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (typeof Toast !== 'undefined') {
            Toast.error('Có lỗi xảy ra khi xuất CV');
        } else {
            alert('Có lỗi xảy ra khi xuất CV');
        }
    } finally {
        hideLoading();
    }
}

// Show export format dialog
function showExportFormatDialog() {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'modal fade';
        dialog.id = 'exportFormatModal';
        dialog.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header" style="background: var(--gradient-1); color: white;">
                        <h5 class="modal-title">
                            <i class="bi bi-download me-2"></i>Chọn định dạng xuất CV
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="d-grid gap-2">
                            <button class="btn btn-outline-primary btn-lg" onclick="selectFormat('pdf')" style="text-align: left;">
                                <i class="bi bi-file-pdf me-2"></i>
                                <strong>PDF</strong>
                                <br>
                                <small>Định dạng phổ biến, dễ in và chia sẻ</small>
                            </button>
                            <button class="btn btn-outline-success btn-lg" onclick="selectFormat('docx')" style="text-align: left;">
                                <i class="bi bi-file-word me-2"></i>
                                <strong>DOCX</strong>
                                <br>
                                <small>Microsoft Word, dễ chỉnh sửa</small>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
        const modal = new bootstrap.Modal(dialog);
        modal.show();
        
        window.selectFormat = (format) => {
            modal.hide();
            setTimeout(() => {
                document.body.removeChild(dialog);
                delete window.selectFormat;
            }, 300);
            resolve(format);
        };
        
        dialog.addEventListener('hidden.bs.modal', () => {
            if (window.selectFormat) {
                document.body.removeChild(dialog);
                delete window.selectFormat;
                resolve(null);
            }
        });
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'success' ? 'success' : 'info'} position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
            <span>${message}</span>
        </div>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('fade');
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}


// Collect form data
function collectFormData() {
    // Experiences
    const experiences = [];
    const expCards = document.querySelectorAll('#experiencesContainer .item-card');
    expCards.forEach((card, idx) => {
        experiences.push({
            position: document.querySelector(`input[name="exp_position_${idx}"]`)?.value || '',
            company: document.querySelector(`input[name="exp_company_${idx}"]`)?.value || '',
            start_date: document.querySelector(`input[name="exp_start_${idx}"]`)?.value || '',
            end_date: document.querySelector(`input[name="exp_end_${idx}"]`)?.value || '',
            is_current: document.querySelector(`input[name="exp_current_${idx}"]`)?.checked || false,
            description: document.querySelector(`textarea[name="exp_description_${idx}"]`)?.value || ''
        });
    });

    // Education
    const education = [];
    const eduCards = document.querySelectorAll('#educationContainer .item-card');
    eduCards.forEach((card, idx) => {
        education.push({
            school: document.querySelector(`input[name="edu_school_${idx}"]`)?.value || '',
            major: document.querySelector(`input[name="edu_major_${idx}"]`)?.value || '',
            degree: document.querySelector(`select[name="edu_degree_${idx}"]`)?.value || '',
            year: document.querySelector(`input[name="edu_year_${idx}"]`)?.value || ''
        });
    });

    // Skills
    const skillsElem = document.getElementById('skillsText');
    const skillsText = skillsElem ? skillsElem.value : '';
    const skills = skillsText
        ? skillsText.split(/[,\n]/).map(s => s.trim()).filter(s => s)
        : [];

    // Certifications
    const certifications = [];
    const certCards = document.querySelectorAll('#certificationsContainer .item-card');
    certCards.forEach((card, idx) => {
        certifications.push({
            name: document.querySelector(`input[name="cert_name_${idx}"]`)?.value || '',
            organization: document.querySelector(`input[name="cert_org_${idx}"]`)?.value || '',
            date: document.querySelector(`input[name="cert_date_${idx}"]`)?.value || ''
        });
    });

    // Projects
    const projects = [];
    const projCards = document.querySelectorAll('#projectsContainer .item-card');
    projCards.forEach((card, idx) => {
        projects.push({
            name: document.querySelector(`input[name="proj_name_${idx}"]`)?.value || '',
            url: document.querySelector(`input[name="proj_url_${idx}"]`)?.value || '',
            description: document.querySelector(`textarea[name="proj_description_${idx}"]`)?.value || ''
        });
    });

    // Languages
    const languages = [];
    const langCards = document.querySelectorAll('#languagesContainer .item-card');
    langCards.forEach((card, idx) => {
        languages.push({
            name: document.querySelector(`input[name="lang_name_${idx}"]`)?.value || '',
            level: document.querySelector(`select[name="lang_level_${idx}"]`)?.value || ''
        });
    });

    // Personal info
    const fullNameElem = document.getElementById('fullName');
    const emailElem = document.getElementById('email');
    const phoneElem = document.getElementById('phone');
    const addressElem = document.getElementById('address');
    const dobElem = document.getElementById('dateOfBirth');
    const linkedinElem = document.getElementById('linkedin');
    const websiteElem = document.getElementById('website');
    const summaryElem = document.getElementById('summaryText');
    const avatarElem = document.getElementById('avatar');
    
    // Lấy avatar URL nếu đã upload
    let avatarUrl = '';
    if (avatarElem && avatarElem.files && avatarElem.files[0]) {
        // Nếu có file mới, sẽ upload riêng
        avatarUrl = window.currentAvatarUrl || '';
    } else {
        // Nếu không có file mới, dùng URL đã lưu
        avatarUrl = window.currentAvatarUrl || '';
    }

    return {
        id: currentCVId,
        full_name: fullNameElem ? fullNameElem.value : '',
        email: emailElem ? emailElem.value : '',
        phone: phoneElem ? phoneElem.value : '',
        address: addressElem ? addressElem.value : '',
        date_of_birth: dobElem ? dobElem.value : '',
        linkedin: linkedinElem ? linkedinElem.value : '',
        website: websiteElem ? websiteElem.value : '',
        summary: summaryElem ? summaryElem.value : '',
        avatar_url: avatarUrl,
        experiences: experiences,
        education: education,
        skills: skills,
        certifications: certifications,
        projects: projects,
        languages: languages,
        template: document.querySelector('input[name="template"]:checked')?.value || 'classic'
    };
}


// Preview CV
async function previewCV() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        if (typeof Toast !== 'undefined') {
            Toast.warning('Vui lòng đăng nhập để xem trước CV');
        } else {
            alert('Vui lòng đăng nhập để xem trước CV');
        }
        window.location.href = '/login';
        return;
    }

    // Save form data before preview
    saveFormDataToLocalStorage();

    const formData = collectFormData();
    
    // Debug: Log data để kiểm tra
    console.log('Summary data:', formData.summary);
    console.log('Summary element:', document.getElementById('summaryText'));
    console.log('Summary value:', document.getElementById('summaryText')?.value);
    console.log('Skills data:', formData.skills);
    console.log('Skills element:', document.getElementById('skillsText'));
    console.log('Skills value:', document.getElementById('skillsText')?.value);
    console.log('Full formData:', formData);
    
    // Validate required fields
    if (!formData.full_name) {
        if (typeof Toast !== 'undefined') {
            Toast.warning('Vui lòng nhập họ tên');
        } else {
            alert('Vui lòng nhập họ tên');
        }
        return;
    }

    showLoading();

    try {
        // Upload avatar nếu có file mới
        const avatarInput = document.getElementById('avatar');
        if (avatarInput && avatarInput.files && avatarInput.files[0]) {
            const avatarFormData = new FormData();
            avatarFormData.append('avatar', avatarInput.files[0]);
            
            const avatarResponse = await fetch('/api/cv-builder/upload-avatar', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                },
                body: avatarFormData
            });
            
            if (avatarResponse.ok) {
                const avatarData = await avatarResponse.json();
                if (avatarData.success && avatarData.avatar_url) {
                    formData.avatar_url = avatarData.avatar_url;
                    window.currentAvatarUrl = avatarData.avatar_url;
                }
            }
        }
        
        // Gửi FormData nếu có ảnh, JSON nếu không
        let response;
        if (avatarInput && avatarInput.files && avatarInput.files[0] && formData.avatar_url) {
            // Nếu đã upload ảnh, gửi JSON với avatar_url
            response = await fetch('/api/cv-builder/preview-temp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(formData)
            });
        } else {
            // Gửi JSON bình thường
            response = await fetch('/api/cv-builder/preview-temp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(formData)
        });
        }

        if (response.ok) {
            const html = await response.text();
            
            // Mở modal trước để iframe được render
            const previewModalElement = document.getElementById('previewModal');
            const previewModal = new bootstrap.Modal(previewModalElement);
            previewModal.show();
            
            // Đợi modal hiển thị xong rồi mới load iframe
            previewModalElement.addEventListener('shown.bs.modal', function loadIframe() {
                // Hiển thị preview trong iframe để cách ly CSS
                const previewIframe = document.getElementById('previewContent');
                
                try {
                    const iframeDoc = previewIframe.contentDocument || previewIframe.contentWindow.document;
                    
                    // Ghi HTML vào iframe
                    iframeDoc.open();
                    iframeDoc.write(html);
                    iframeDoc.close();
                } catch (e) {
                    console.error('Error loading iframe:', e);
                    // Fallback: nếu iframe không hoạt động, dùng srcdoc
                    previewIframe.srcdoc = html;
                }
                
                // Remove event listener sau khi đã load
                previewModalElement.removeEventListener('shown.bs.modal', loadIframe);
            }, { once: true });
            
            // Lưu formData để dùng cho export
            window.previewFormData = formData;
            
            // Restore form data when modal is closed
            const handleModalClose = () => {
                // Xóa nội dung iframe để tránh CSS ảnh hưởng
                try {
                    const previewIframe = document.getElementById('previewContent');
                    const iframeDoc = previewIframe.contentDocument || previewIframe.contentWindow.document;
                    iframeDoc.open();
                    iframeDoc.write('');
                    iframeDoc.close();
                } catch (e) {
                    // Nếu không thể xóa iframe, dùng srcdoc
                    const previewIframe = document.getElementById('previewContent');
                    if (previewIframe) {
                        previewIframe.srcdoc = '';
                    }
                }
                
                // Khôi phục dữ liệu từ localStorage khi đóng modal
                restoreFormDataFromLocalStorage();
                // Remove event listener sau khi đã xử lý
                previewModalElement.removeEventListener('hidden.bs.modal', handleModalClose);
            };
            previewModalElement.addEventListener('hidden.bs.modal', handleModalClose);
        } else {
            const data = await response.json();
            if (typeof Toast !== 'undefined') {
                Toast.error('Lỗi: ' + (data.message || 'Không thể preview CV'));
            } else {
                alert('Lỗi: ' + (data.message || 'Không thể preview CV'));
            }
        }
    } catch (error) {
        console.error('Error:', error);
        if (typeof Toast !== 'undefined') {
            Toast.error('Có lỗi xảy ra khi preview CV');
        } else {
            alert('Có lỗi xảy ra khi preview CV');
        }
    } finally {
        hideLoading();
    }
}

// Export CV from preview modal
async function exportFromPreview() {
    if (!window.previewFormData) {
        if (typeof Toast !== 'undefined') {
            Toast.warning('Không có dữ liệu CV để xuất');
        } else {
            alert('Không có dữ liệu CV để xuất');
        }
        return;
    }
    
    // Đóng modal trước
    const previewModal = bootstrap.Modal.getInstance(document.getElementById('previewModal'));
    if (previewModal) {
        previewModal.hide();
    }
    
    // Gọi hàm export
    await exportCV();
}


// Loading overlay
function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

// Get storage key for current user
function getStorageKey() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
        // Nếu chưa đăng nhập, không lưu dữ liệu
        return null;
    }
    return `cv_builder_draft_${userId}`;
}

// Auto-save to localStorage (chỉ lưu cho user hiện tại)
function saveFormDataToLocalStorage() {
    try {
        const storageKey = getStorageKey();
        if (!storageKey) {
            // Không lưu nếu chưa đăng nhập
            return;
        }
        const formData = collectFormData();
        localStorage.setItem(storageKey, JSON.stringify(formData));
        console.log('Auto-saved CV data to localStorage for user:', localStorage.getItem('user_id'));
    } catch (error) {
        console.error('Error saving to localStorage:', error);
    }
}

// Restore form data from localStorage (chỉ restore cho user hiện tại)
function restoreFormDataFromLocalStorage() {
    try {
        const storageKey = getStorageKey();
        if (!storageKey) {
            // Không restore nếu chưa đăng nhập
            return;
        }
        const savedData = localStorage.getItem(storageKey);
        if (!savedData) return;
        
        const formData = JSON.parse(savedData);
        
        // Restore personal info
        if (formData.full_name) document.getElementById('fullName').value = formData.full_name;
        if (formData.email) document.getElementById('email').value = formData.email;
        if (formData.phone) document.getElementById('phone').value = formData.phone;
        if (formData.address) document.getElementById('address').value = formData.address;
        if (formData.date_of_birth) document.getElementById('dateOfBirth').value = formData.date_of_birth;
        if (formData.linkedin) document.getElementById('linkedin').value = formData.linkedin;
        if (formData.website) document.getElementById('website').value = formData.website;
        if (formData.summary) document.getElementById('summaryText').value = formData.summary;
        
        // Restore avatar URL (nếu đã upload)
        if (formData.avatar_url) {
            window.currentAvatarUrl = formData.avatar_url;
            const preview = document.getElementById('avatarPreview');
            const placeholder = document.getElementById('avatarPlaceholder');
            if (preview && placeholder) {
                preview.src = formData.avatar_url;
                preview.style.display = 'block';
                placeholder.style.display = 'none';
            }
        }
        
        // Restore skills
        if (formData.skills && formData.skills.length > 0) {
            document.getElementById('skillsText').value = formData.skills.join('\n');
        }
        
        // Restore template
        if (formData.template) {
            const templateRadio = document.querySelector(`input[name="template"][value="${formData.template}"]`);
            if (templateRadio) templateRadio.checked = true;
        }
        
        // Restore experiences
        if (formData.experiences && formData.experiences.length > 0) {
            document.getElementById('experiencesContainer').innerHTML = '';
            experiences = [];
            formData.experiences.forEach((exp, idx) => {
                addExperience();
                const card = document.querySelector(`#experiencesContainer .item-card[data-index="${idx}"]`);
                if (card) {
                    if (exp.position) document.querySelector(`input[name="exp_position_${idx}"]`).value = exp.position;
                    if (exp.company) document.querySelector(`input[name="exp_company_${idx}"]`).value = exp.company;
                    if (exp.start_date) document.querySelector(`input[name="exp_start_${idx}"]`).value = exp.start_date;
                    if (exp.end_date) document.querySelector(`input[name="exp_end_${idx}"]`).value = exp.end_date;
                    if (exp.is_current) {
                        document.querySelector(`input[name="exp_current_${idx}"]`).checked = true;
                        toggleEndDate(idx);
                    }
                    if (exp.description) document.querySelector(`textarea[name="exp_description_${idx}"]`).value = exp.description;
                }
            });
        }
        
        // Restore education
        if (formData.education && formData.education.length > 0) {
            document.getElementById('educationContainer').innerHTML = '';
            education = [];
            formData.education.forEach((edu, idx) => {
                addEducation();
                const card = document.querySelector(`#educationContainer .item-card[data-index="${idx}"]`);
                if (card) {
                    if (edu.school) document.querySelector(`input[name="edu_school_${idx}"]`).value = edu.school;
                    if (edu.major) document.querySelector(`input[name="edu_major_${idx}"]`).value = edu.major;
                    if (edu.degree) document.querySelector(`select[name="edu_degree_${idx}"]`).value = edu.degree;
                    if (edu.year) document.querySelector(`input[name="edu_year_${idx}"]`).value = edu.year;
                }
            });
        }
        
        // Restore certifications
        if (formData.certifications && formData.certifications.length > 0) {
            document.getElementById('certificationsContainer').innerHTML = '';
            certifications = [];
            formData.certifications.forEach((cert, idx) => {
                addCertification();
                const card = document.querySelector(`#certificationsContainer .item-card[data-index="${idx}"]`);
                if (card) {
                    if (cert.name) document.querySelector(`input[name="cert_name_${idx}"]`).value = cert.name;
                    if (cert.organization) document.querySelector(`input[name="cert_org_${idx}"]`).value = cert.organization;
                    if (cert.date) document.querySelector(`input[name="cert_date_${idx}"]`).value = cert.date;
                }
            });
        }
        
        // Restore projects
        if (formData.projects && formData.projects.length > 0) {
            document.getElementById('projectsContainer').innerHTML = '';
            projects = [];
            formData.projects.forEach((proj, idx) => {
                addProject();
                const card = document.querySelector(`#projectsContainer .item-card[data-index="${idx}"]`);
                if (card) {
                    if (proj.name) document.querySelector(`input[name="proj_name_${idx}"]`).value = proj.name;
                    if (proj.url) document.querySelector(`input[name="proj_url_${idx}"]`).value = proj.url;
                    if (proj.description) document.querySelector(`textarea[name="proj_description_${idx}"]`).value = proj.description;
                }
            });
        }
        
        // Restore languages
        if (formData.languages && formData.languages.length > 0) {
            document.getElementById('languagesContainer').innerHTML = '';
            languages = [];
            formData.languages.forEach((lang, idx) => {
                addLanguage();
                const card = document.querySelector(`#languagesContainer .item-card[data-index="${idx}"]`);
                if (card) {
                    if (lang.name) document.querySelector(`input[name="lang_name_${idx}"]`).value = lang.name;
                    if (lang.level) document.querySelector(`select[name="lang_level_${idx}"]`).value = lang.level;
                }
            });
        }
        
        console.log('Restored CV data from localStorage');
    } catch (error) {
        console.error('Error restoring from localStorage:', error);
    }
}

// Clear saved draft (chỉ xóa dữ liệu của user hiện tại)
function clearSavedDraft() {
    const storageKey = getStorageKey();
    if (storageKey) {
        localStorage.removeItem(storageKey);
    }
    // Xóa dữ liệu cũ (không có user_id) nếu có
    localStorage.removeItem('cv_builder_draft');
}

// Clear all CV drafts (dùng khi logout)
function clearAllCVDrafts() {
    // Xóa tất cả keys bắt đầu bằng 'cv_builder_draft_'
    const keysToRemove = [];
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('cv_builder_draft_')) {
            keysToRemove.push(key);
        }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key));
    // Xóa dữ liệu cũ (không có user_id) nếu có
    localStorage.removeItem('cv_builder_draft');
}

// Initialize - add one empty experience and education, then restore saved data
document.addEventListener('DOMContentLoaded', () => {
    // First, add default empty items
    addExperience();
    addEducation();
    
    // Then restore saved data (will overwrite if exists)
    restoreFormDataFromLocalStorage();
    
    // Set up auto-save on input changes (debounced)
    let saveTimeout;
    const form = document.getElementById('cvForm');
    if (form) {
        form.addEventListener('input', () => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                saveFormDataToLocalStorage();
            }, 1000); // Save after 1 second of no typing
        });
        
        form.addEventListener('change', () => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                saveFormDataToLocalStorage();
            }, 500);
        });
    }
    
    // Save before opening preview
    const previewModal = document.getElementById('previewModal');
    if (previewModal) {
        previewModal.addEventListener('show.bs.modal', () => {
            saveFormDataToLocalStorage();
        });
    }
});

