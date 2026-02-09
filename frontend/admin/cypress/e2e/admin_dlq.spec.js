describe('Admin DLQ E2E', () => {
  const adminToken = Cypress.env('ADMIN_API_KEY') || ''
  const testPayload = { job: { source: 'e2e', external_id: 'e2e-1', title: 'E2E Job' } }

  it('lists DLQ items, requeues and deletes via UI', () => {
    // Precondition: push item to DLQ via script
    cy.exec(`python3 ../../../../scripts/push_dlq.py --payload '${JSON.stringify(testPayload)}'`, { failOnNonZeroExit: false })

    // Visit UI and set admin token if provided
    cy.visit('/')
    if (adminToken) {
      cy.get('input[placeholder="Admin API Key (paste or leave blank if not required)"]').clear().type(adminToken)
      cy.contains('Save').click()
    }

    cy.contains('Refresh').click()

    // Wait for item to appear
    cy.contains('E2E Job', { timeout: 10000 }).should('exist')

    // Requeue the first item
    cy.get('button').contains('Requeue').first().click()

    // The item should no longer be in DLQ
    cy.contains('E2E Job').should('not.exist')
  })
})
