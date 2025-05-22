<script>
import { defineComponent, ref } from 'vue';
import { CdxTable, CdxButton, CdxDialog, CdxField, CdxIcon, CdxMessage, CdxTextArea, CdxInfoChip, CdxProgressIndicator } from '@wikimedia/codex';
import { cdxIconJournal } from '@wikimedia/codex-icons';

export default defineComponent( {
    name: 'Permissions',
    components: {CdxTable, CdxButton, CdxDialog, CdxField, CdxIcon, CdxMessage, CdxTextArea, CdxInfoChip, CdxProgressIndicator},
    methods: {
        async getData() {
        /* Fetch the users SSH keys */
        const res = await fetch("/accounts/api/user");
        const finalRes = await res.json();
        this.userId = finalRes['id']
        this.permissions = finalRes['permissions']
        this.isLoading = false
      },
      onDefaultAction() {
        /* Default (close) action for dialogs should clear various fields and states */
        this.requestReason = ''
        this.open = false
        this.view_logs = false
        this.view_title = ''
      },
      async onPrimaryAction() {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const body = { user: this.userId, system: this.permission.source, key: this.permission.key, comment: this.requestReason}
        const url = "/permissions/api/requests/"
        const requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(body)
        }

        const response = await fetch(url, requestOptions)
        if(!response.ok){
            if(response.status == 403) {
                const msg = await response.text()
                this.errorMessage = msg
            } else {
                const data = await response.json()
                this.errorMessage = data['comment'][0]
            }
            this.open = false
            return
        }

        this.requestReason = ''
        this.open = false
        this.view_logs = false
        this.permission = null
        this.errorMessage = null
        this.getData()

      },
      async viewLog( row ){
        const res = await fetch("/permissions/api/requests/" + row.request );
        const finalRes = await res.json()
        this.logs = finalRes['logs'];
        this.view_title = 'Approval / Rejection log for ' + row.name + " access request."
        this.view_logs = true
      },
      formatDate( date_str ){
        const d = new Date(date_str)
        return d.toDateString() + " " + d.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', hourCycle: 'h24',});
      }
    },
    mounted() {
      this.getData()
    },
    data() {
        return {
            permissions: [],
            permission: null,
            open: false,
            view_logs: false,
            logs: [],
            userId: null,
            errorMessage: null,
            view_title: '',
            request_deny_states: ['AP', 'SY', 'PN'], /* States for which we do not show the "Request" button. */
            isLoading: true
        }
    },
    setup() {
        const requestReason = ref( '' )
        const request_title = ref('Request access to permission')

        /* Actions */
        const defaultAction = {
			label: 'Close'
		};

        const primaryAction = {
			label: 'Submit',
			actionType: 'progressive'
		};

        /* Table columns */
		const columns = [
			{ id: 'name', label: 'Permission' },
            { id: 'description', label: 'Description'},
            { id: 'status', label: 'Status'},
            { id: 'actions', label: '', minWidth: '300px'},
		];

        /* Table columns */
		const log_columns = [
            { id: 'approved', label: 'Status'},
            { id: 'created', label: 'Created', minWidth: '200px' },
			{ id: 'username', label: 'Manager', minWidth: '100px' },
            { id: 'comment', label: 'Comment', minWidth: '320px' },
		];

        /* functions for accessing dialogs via table actions */
        function requestPerm( row ) {
            this.permission = row
            this.request_title = "Request access to " + row.name
            this.open = true
		}

        return {
            columns,
            log_columns,
            defaultAction,
            primaryAction,
            requestPerm,
            request_title,
            requestReason,
            cdxIconJournal
        }
    }
});
</script>

<template>
    <div v-if="isLoading" class="loader d-flex justify-content-center align-middle">
        <cdx-progress-indicator show-label>Loading permissions</cdx-progress-indicator>
    </div>


    <cdx-message v-if="errorMessage" type="error" :fade-in="true">
        <p><strong>Error!</strong> {{ errorMessage }}</p>
  </cdx-message>
  <br>

    <cdx-table v-if="!isLoading" class="cdx-docs-table-custom-cells" caption="Permissions" :columns="columns" :data="permissions">
        <!-- System column e.g. WMCS/LDAP/Puppet -->
        <template #item-source_display="{ item }">
            {{ item }}
    	</template>

		<!-- Truncated ssh key, key data is stored in data variable, therefor item-data -->
		<template #item-name="{ item }">
            {{ item }}
		</template>

		<template #item-status="{ row }">
            <cdx-info-chip v-if="row.state == 'AP'" status="success">
				{{ row.status_display }}
		    </cdx-info-chip>
            <cdx-info-chip v-else-if="row.state == 'SY'" status="success">
				Approved
		    </cdx-info-chip>
            <cdx-info-chip v-else-if="row.state == 'RJ'" status="error">
				{{ row.status_display }}
		    </cdx-info-chip>
            <span v-else>
                {{ row.status_display }}
            </span>
		</template>

		<template #item-actions="{ row }">
            <div class="cdx-table__table__cell--align-number">
            <cdx-button v-if="!row.existing && request_deny_states.indexOf(row.state) == -1 " action="progressive" weight="primary" @click="requestPerm( row )">
				Request
			</cdx-button>
            &nbsp;
            <cdx-button v-if="row.request" weight="quiet" aria-label="Log" @click="viewLog( row )">
				View log
			</cdx-button>
            </div>
		</template>
	</cdx-table>

    <cdx-dialog
			v-model:open="open"
			class="cdx-demo-dialog-form-inputs"
			:title=request_title
			:use-close-button="true"
			:default-action="defaultAction"
			:primary-action="primaryAction"
			@default="open = false"
            @primary="onPrimaryAction"
		>
        <p class="permission_dialog">
            {{ permission.description }}
        </p>
			<cdx-field>
				<template #label>
					Reason for request
				</template>
				<cdx-text-area
					v-model="requestReason"
					class="cdx-demo-dialog-form-inputs__text-input"
				/>
			</cdx-field>
		</cdx-dialog>

    <cdx-dialog
			v-model:open="view_logs"
			:title=view_title
			:use-close-button="true"
			:primaryActionDisabled="true"
			:default-action="defaultAction"
			@default="view_logs = false"
            class="dialog_logs"
		>
	<cdx-table
		:columns="log_columns"
		:data="logs"
        caption=""
        :hideCaption="true"
		:use-row-headers="false"
	>
    <template #empty-state> There is no data available.</template>
    <template #item-approved="{ item }">
        <cdx-info-chip v-if="item" status="success">
				Approved
		</cdx-info-chip>
        <cdx-info-chip v-else status="error">
				Rejected
		</cdx-info-chip>
    </template>
    <template #item-created="{ item }">
        {{ formatDate(item) }}
    </template>
	</cdx-table>
	</cdx-dialog>

</template>

<style>
/* We're putting the logs into a table, within the dialog,
   this means that the default max-width of 32rem is a bit
   to small, and will in many cases trigger a horizontal
   scroll within the dialog. Increasing to 64rem gives us
   the space needed to show the table with all the columns.
*/
.cdx-dialog:has(table) {
    max-width: 64rem;
}

.loader {
  top: 50%;
  height: 50vh;
}

</style>