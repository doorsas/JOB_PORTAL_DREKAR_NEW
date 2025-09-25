document.addEventListener('DOMContentLoaded', function() {
    var clientTypeField = document.getElementById('id_client_type');
    var clientObjectField = document.getElementById('id_client_object_id');

    if (clientTypeField && clientObjectField) {
        clientTypeField.addEventListener('change', function() {
            var contentTypeId = this.value;

            if (contentTypeId) {
                // Clear current options
                clientObjectField.innerHTML = '<option value="">Select client</option>';
                clientObjectField.disabled = false;

                // Fetch available clients for the selected content type
                fetch('/admin/core/get_clients_for_type/' + contentTypeId + '/')
                    .then(response => response.json())
                    .then(data => {
                        data.forEach(function(client) {
                            var option = document.createElement('option');
                            option.value = client.id;
                            option.textContent = client.name;
                            clientObjectField.appendChild(option);
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching clients:', error);
                    });
            } else {
                clientObjectField.innerHTML = '<option value="">Select client type first</option>';
                clientObjectField.disabled = true;
            }
        });

        // Initialize on page load
        if (clientTypeField.value) {
            clientTypeField.dispatchEvent(new Event('change'));
        } else {
            clientObjectField.disabled = true;
        }
    }
});