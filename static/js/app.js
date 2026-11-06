// LabTrace Frontend Interactions
document.addEventListener('DOMContentLoaded', () => {
    // 1. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // 2. View Equipment Details Modal
    const viewDetailModalEl = document.getElementById('viewDetailModal');
    if (viewDetailModalEl) {
        viewDetailModalEl.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const equipmentId = button.getAttribute('data-eq-id');
            
            // Populate loading state
            document.getElementById('viewModalTitle').textContent = 'Loading Equipment...';
            document.getElementById('viewTag').textContent = '...';
            document.getElementById('viewName').textContent = '...';
            document.getElementById('viewModel').textContent = '...';
            document.getElementById('viewSerial').textContent = '...';
            document.getElementById('viewCategory').textContent = '...';
            document.getElementById('viewLab').textContent = '...';
            document.getElementById('viewCost').textContent = '...';
            document.getElementById('viewDate').textContent = '...';
            document.getElementById('viewStatus').textContent = '...';
            document.getElementById('viewCondition').textContent = '...';
            document.getElementById('viewSupplier').textContent = '...';
            document.getElementById('viewSupplierContact').textContent = '...';

            fetch(`/equipment/${equipmentId}/json`)
                .then(response => {
                    if (!response.ok) throw new Error('Network response error');
                    return response.json();
                })
                .then(data => {
                    document.getElementById('viewModalTitle').textContent = data.name;
                    document.getElementById('viewTag').textContent = data.asset_tag;
                    document.getElementById('viewName').textContent = data.name;
                    document.getElementById('viewModel').textContent = data.model || 'N/A';
                    document.getElementById('viewSerial').textContent = data.serial_number || 'N/A';
                    document.getElementById('viewCategory').textContent = data.category_name;
                    document.getElementById('viewLab').textContent = `${data.lab_name} (${data.room_number}, ${data.building})`;
                    document.getElementById('viewCost').textContent = `$${Number(data.cost).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                    document.getElementById('viewDate').textContent = data.purchase_date || 'N/A';
                    document.getElementById('viewStatus').textContent = data.status;
                    document.getElementById('viewCondition').textContent = data.condition_state;
                    document.getElementById('viewSupplier').textContent = data.supplier_name || 'Unassigned';
                    
                    const contact = [];
                    if (data.supplier_contact) contact.push(data.supplier_contact);
                    if (data.supplier_phone) contact.push(data.supplier_phone);
                    if (data.supplier_email) contact.push(data.supplier_email);
                    document.getElementById('viewSupplierContact').textContent = contact.join(' | ') || 'N/A';
                })
                .catch(err => {
                    console.error('Error loading equipment:', err);
                    document.getElementById('viewModalTitle').textContent = 'Error Loading Asset';
                });
        });
    }

    // 3. Edit Equipment Modal
    const editModalEl = document.getElementById('editEquipmentModal');
    if (editModalEl) {
        editModalEl.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const equipmentId = button.getAttribute('data-eq-id');
            const form = document.getElementById('editEquipmentForm');
            form.action = `/equipment/${equipmentId}/edit`;

            fetch(`/equipment/${equipmentId}/json`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('edit_name').value = data.name;
                    document.getElementById('edit_asset_tag').value = data.asset_tag;
                    document.getElementById('edit_category_id').value = data.category_id;
                    document.getElementById('edit_lab_id').value = data.lab_id;
                    document.getElementById('edit_supplier_id').value = data.supplier_id || '';
                    document.getElementById('edit_model').value = data.model || '';
                    document.getElementById('edit_serial_number').value = data.serial_number || '';
                    document.getElementById('edit_purchase_date').value = data.purchase_date || '';
                    document.getElementById('edit_cost').value = data.cost || '0.00';
                    document.getElementById('edit_status').value = data.status;
                    document.getElementById('edit_condition_state').value = data.condition_state;
                })
                .catch(err => console.error('Error pre-populating edit modal:', err));
        });
    }

    // 4. Delete Confirmation Modal
    const deleteModalEl = document.getElementById('deleteConfirmModal');
    if (deleteModalEl) {
        deleteModalEl.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            const equipmentId = button.getAttribute('data-eq-id');
            const assetName = button.getAttribute('data-eq-name');
            const assetTag = button.getAttribute('data-eq-tag');

            document.getElementById('deleteAssetName').textContent = `${assetName} (${assetTag})`;
            document.getElementById('deleteEquipmentForm').action = `/equipment/${equipmentId}/delete`;
        });
    }
});

