<script>
import { defineComponent, ref } from 'vue';
import { CdxTable, CdxButton, CdxIcon, CdxDialog, CdxField, CdxTextArea, CdxSelect } from '@wikimedia/codex';
import { cdxIconEdit, cdxIconTrash, cdxIconEye } from '@wikimedia/codex-icons';

export default defineComponent( {
	name: 'SSHKeyManagement',
	components: { CdxTable, CdxButton, CdxIcon, CdxDialog, CdxField, CdxTextArea, CdxSelect },
    data() {
      return {
        listItems: [],
        userId: null,
        systemsItems: [],
        delete_target: null,
        edit_target: null,
        view_target: null
      }
    },
    mounted() {
      this.getData()
    },
    methods: {
      async getData() {
        /* Fetch the users SSH keys */
        const res = await fetch("/accounts/api/user");
        const finalRes = await res.json();
        this.listItems = finalRes['ssh_keys'];
        this.userId = finalRes['id']

        /* Map backends data to structure usable by Codex select field */
        this.systemsItems = Object.entries(finalRes['backends']).map(([key, value]) => ({ label: value, value:key }))

        /* Select the first system as the default */
        this.selected = this.systemsItems[0].value
      },
      onDefaultAction() {
        /* Default (close) action for dialogs should clear various fields and states */
        this.keyStatus = 'default'
        this.inputValue = ''
        this.open = false
        this.edit = false
      },
      onDeleteAction(){
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const requestOptions = {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
        }

        const uuid = this.delete_target.uuid
        // TODO: Add error handling
        fetch("/accounts/api/ssh/" + this.delete_target.uuid, requestOptions)
        this.listItems.forEach(function(elm, i, arr){
            if( elm.uuid == uuid){
                arr.splice(i, 1)
            }
        })

        this.confirm = false
        this.delete_target = null
      },
      onKeyInput(){
        // When adding an SSH key there might be a previous validation error, clear that out as the user starts typing
        this.keyStatus = "default"
      },
      async onPrimaryAction() {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        let url = "/accounts/api/ssh"
        let method = 'POST'
        let body = { user: this.userId , data: this.inputValue, system: this.selected}
        if( this.edit_target ) {
            body['system'] = this.selected
            body['data'] = this.edit_target.data
            url = url + "/" + this.edit_target.uuid
            method = 'PUT'
        }
        const requestOptions = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(body)
        }

        const response = await fetch(url, requestOptions)
        const data = await response.json()
        if(!response.ok){
            console.log(data)
            if('data' in data) {
                this.keyMessages['error'] = data['data'][0]
                this.keyStatus = 'error'
            }

        } else {
            this.getData()
            this.edit_target = null
            this.inputValue = ''
            this.keyStatus = 'default'
            this.open = false
            this.edit = false
        }}
    },
	setup() {
        /* State variables */
        const open = ref( false )
        const edit = ref( false )
        const confirm = ref( false )
        const view = ref( null )
        const selected = ref( null )
        const inputValue = ref( '' )
        const keyMessages = ref( {error: 'Invalid key'} )
        const keyStatus = ref('default')
        const view_title = ref('SSH Key')

        /* Actions */
        const defaultAction = {
			label: 'Close'
		};

        const primaryAction = {
			label: 'Save',
			actionType: 'progressive'
		};

        const deleteAction = {
			label: 'Delete',
			actionType: 'destructive'
		};

        /* Table columns */
		const columns = [
			{ id: 'system_display', label: 'System' },
			{ id: 'data', label: 'Key' },
            { id: 'actions', label: 'Actions' }
		];

        /* functions for accessing dialogs via table actions */
        function editKey( row ) {
            this.edit_target = row
            this.edit = true
		}

        function removeKey( row ) {
            this.delete_target = row
            this.confirm = true
		}

        function viewKey( item ) {
            this.view_target = item
            this.view_title = "Key (" + item.type + ")"
            if(item.system){
                this.view_title = item.system_display
            }
			this.view = true
		}

        /* Truncate SSH keys to save space on the page */
        function truncateKey(key){
            return key.slice(0, 50) + "..."
        }


		return {
            open,
            edit,
            view,
            confirm,
            selected,
            inputValue,
            keyMessages,
            keyStatus,
            view_title,
            primaryAction,
            deleteAction,
            defaultAction,
			columns,
			cdxIconEdit,
			cdxIconTrash,
            cdxIconEye,
			editKey,
			removeKey,
            viewKey,
            truncateKey
		};
	}
} );
</script>

<template>

    <!-- Table of SSH keys -->
    <cdx-table class="cdx-docs-table-custom-cells" caption="Your SSH keys" :columns="columns" :data="listItems">
        <template #header>
			<div class="cdx-docs-table-with-selection__header-content">
				<span class="cdx-docs-table-with-selection__header-content__buttons">
					<cdx-button @click="open = true">
						Add new key
					</cdx-button>
				</span>
			</div>
		</template>

        <!-- System column e.g. WMCS/LDAP/Puppet -->
        <template #item-system_display="{ item }">
            {{ item }}
    	</template>

		<!-- Truncated ssh key, key data is stored in data variable, therefor item-data -->
		<template #item-data="{ item }">
            <span style="word-break: break-all;">{{ truncateKey(item) }}</span>
		</template>

		<!-- Setup action "buttons". Codex guide recommends not using buttons here -->
		<template #item-actions="{ row }">
			<div class="cdx-docs-table-custom-cells__actions">
				<cdx-button weight="quiet" aria-label="Edit" @click="editKey( row )">
                    <cdx-icon :icon="cdxIconEdit" />
                </cdx-button>

                <cdx-button weight="quiet" aria-label="View full" @click="viewKey( row )">
                    <cdx-icon :icon="cdxIconEye" />
                </cdx-button>

				<cdx-button weight="quiet" action="destructive" aria-label="Remove" @click="removeKey( row )">
					<cdx-icon :icon="cdxIconTrash" />
				</cdx-button>
			</div>
		</template>
	</cdx-table>

    <!-- New key dialog -->
    <cdx-dialog v-model:open="open" class="cdx-dialog-form-inputs" title="Upload new SSH key" :use-close-button="true" :default-action="defaultAction" :primary-action="primaryAction" @primary="onPrimaryAction" @default="onDefaultAction">
	    <cdx-field :status="keyStatus" :messages="keyMessages">
	        <template #labele>Key</template>
            <!-- bump rows to 18, to ensure enough height to properly show an RSA key -->
    		<cdx-text-area v-model="inputValue" rows="18" class="cdx-demo-dialog-form-inputs__text-input" @input="onKeyInput"/>
	    </cdx-field>
	    <cdx-field>
	        <template #label>System</template>
		    <cdx-select v-model:selected="selected" class="cdx-demo-dialog-form-inputs__select" :menu-items="systemsItems" />
	    </cdx-field>
    </cdx-dialog>

    <!-- Edit dialog / assign system -->
    <cdx-dialog v-model:open="edit" class="cdx-dialog-form-inputs" title="Select where to use your SSH key" :use-close-button="true" :default-action="defaultAction" :primary-action="primaryAction" @primary="onPrimaryAction" @default="onDefaultAction">
	    <cdx-field>
	        <template #label>System</template>
		    <cdx-select v-model:selected="selected" class="cdx-demo-dialog-form-inputs__select" :menu-items="systemsItems" />
	    </cdx-field>
    </cdx-dialog>

    <!-- Delete SSH key dialog -->
    <cdx-dialog
			v-model:open="confirm"
			title="Delete key?"
			:use-close-button="true"
			:stacked-actions="true"
			:primary-action="deleteAction"
			:default-action="defaultAction"
			@primary="onDeleteAction"
			@default="confirm = false"
            prop-delete-target=delete_target
		>
        <p>
        <strong>This is a destructive action.</strong><br>
        <strong>Deleted keys cannot be recovered!</strong>
        </p>
        <p>Confirm that you wish to delete the following key:</p>
        <code>{{ delete_target.data }}</code>
	</cdx-dialog>

    <!-- Display full SSH key -->
    <cdx-dialog
			v-model:open="view"
			:title="view_title"
			:use-close-button="true"
            primaryActionDisabled="true"
            useDefaultAction="true"
			:default-action="defaultAction"
			@default="view = false"
		>
        <code>{{ view_target.data }}</code>
    </cdx-dialog>

</template>