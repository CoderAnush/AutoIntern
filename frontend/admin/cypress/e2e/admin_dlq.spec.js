describe('Admin DLQ E2E', () => {
  const adminToken = Cypress.env('ADMIN_API_KEY') || ''
  const testPayload = { job: { source: 'e2e', external_id: 'e2e-1', title: 'E2E Job' } }

  it('lists DLQ items, requeues and processes end-to-end', () => {
    // Precondition: push item to DLQ via script
    cy.exec(`python3 ../../../../scripts/push_dlq.py --payload '${JSON.stringify(testPayload)}'`, { failOnNonZeroExit: false })

    // Visit UI and set admin token if provided
    cy.visit('/')
    if (adminToken) {
      cy.get('input[placeholder="Admin API Key (paste or leave blank if not required)"]').clear().type(adminToken)
      cy.contains('Save').click()
    }

    cy.contains('Refresh').click()

    // Wait for item to appear in DLQ UI
    cy.contains('E2E Job', { timeout: 10000 }).should('exist')

    // Requeue the first item
    cy.get('button').contains('Requeue').first().click()

    // The item should no longer be in DLQ UI
    cy.contains('E2E Job').should('not.exist')

    // Poll the API (worker should process the requeued item) until the job appears
    cy.log('Polling API for processed job...')
    const apiUrl = 'http://localhost:8000/jobs?external_id=e2e-1'

    const checkJob = () => {
      return cy.request({ url: apiUrl, failOnStatusCode: false }).then((r) => {
        if (r.status === 200 && Array.isArray(r.body) && r.body.length > 0) {
          expect(r.body[0].external_id).to.equal('e2e-1')
          return
        }
        cy.wait(2000)
        return checkJob()
      })
    }

    checkJob().then(() => {
      // Additionally verify the job is indexed in Elasticsearch
      cy.log('Polling Elasticsearch for indexed document...')
      const esSearch = () => {
        return cy.request({ url: 'http://localhost:9200/autointern-jobs/_search?q=external_id:e2e-1', failOnStatusCode: false }).then((r) => {
          if (r.status === 200 && r.body && r.body.hits && r.body.hits.total && r.body.hits.total.value > 0) {
            expect(r.body.hits.hits[0]._source.external_id).to.equal('e2e-1')
            return
          }
          cy.wait(2000)
          return esSearch()
        })
      }

      esSearch()
    })
  })
})
