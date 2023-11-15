import { computed, ref } from 'vue'
import axios from 'axios'
import sqlPrettier from 'sql-prettier'
import { useDatabases } from './databases'
import router from '../router'

const { selectDatabaseById, databaseSelectedId } = useDatabases()

export const queryRef = ref(null)
export const queryText = ref('')
export const queryId = ref<number | null>(null)
export const querySQL = ref('')
export const queryResults = ref(null)
export const queryCount = ref(null)
export const queryError = ref(null)
export const loading = ref(false)
export const visualisationParams = ref(null)

export const loadQuery = async (id: number) => {
  queryId.value = id
  const response = await axios.get(`/api/query/${id}`)

  const query = response.data
  queryRef.value = query
  queryText.value = query.query
  visualisationParams.value = query.visualisationParams
  await selectDatabaseById(query.databaseId)

  if (query.sql) {
    querySQL.value = query.sql
  }
  if (querySQL.value) {
    runQuery()
  }
}

export const executeQuery = async (
  databaseId: number,
  sql: string
): Promise<{ rows: any[]; count: number }> => {
  return await axios
    .post('/api/query/_run', {
      query: sql,
      databaseId: databaseId
    })
    .then((response) => {
      return {
        rows: response.data.rows as any[],
        count: response.data.count as number
      }
    })
    .catch((e) => {
      throw new Error(e.response.data.message)
    })
}

export const runQuery = async () => {
  loading.value = true
  // @ts-ignore
  return executeQuery(databaseSelectedId.value, querySQL.value)
    .then(({ rows, count }) => {
      queryError.value = null
      // @ts-ignore
      queryResults.value = rows
      // @ts-ignore
      queryCount.value = count
      return queryResults.value
    })
    .catch((message) => {
      queryError.value = message
    })
    .finally(() => {
      loading.value = false
    })
}

export const updateQuery = async () => {
  if (queryId.value) {
    await axios.put(`/api/query/${queryId.value}`, {
      query: queryText.value,
      sql: querySQL.value,
      visualisationParams: visualisationParams.value
    })
  } else {
    const response = await axios.post('/api/query', {
      query: queryText.value,
      sql: querySQL.value,
      databaseId: databaseSelectedId.value,
      visualisationParams: visualisationParams.value
    })
    queryId.value = response.data.id
    router.push({ name: 'Query', params: { id: queryId.value } })
  }
  loadQuery(queryId.value as number)
}

export const updateVisualisationParams = async (params: any) => {
  visualisationParams.value = params
}

export const queryIsModified = computed(() => {
  return (
    querySQL.value !== queryRef.value?.sql ||
    queryText.value !== queryRef.value?.query ||
    JSON.stringify(visualisationParams.value) !==
      JSON.stringify(queryRef.value?.visualisationParams)
  )
})
