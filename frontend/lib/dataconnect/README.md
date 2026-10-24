# Generated TypeScript README
This README will guide you through the process of using the generated JavaScript SDK package for the connector `default`. It will also provide examples on how to use your generated SDK to call your Data Connect queries and mutations.

***NOTE:** This README is generated alongside the generated SDK. If you make changes to this file, they will be overwritten when the SDK is regenerated.*

# Table of Contents
- [**Overview**](#generated-javascript-readme)
- [**Accessing the connector**](#accessing-the-connector)
  - [*Connecting to the local Emulator*](#connecting-to-the-local-emulator)
- [**Queries**](#queries)
  - [*GetCurrentUser*](#getcurrentuser)
  - [*GetMySupplierProfile*](#getmysupplierprofile)
  - [*ListMySavedTenders*](#listmysavedtenders)
- [**Mutations**](#mutations)
  - [*UpsertUser*](#upsertuser)
  - [*CreateSupplierProfile*](#createsupplierprofile)
  - [*SaveTender*](#savetender)
  - [*DeleteSavedTender*](#deletesavedtender)

# Accessing the connector
A connector is a collection of Queries and Mutations. One SDK is generated for each connector - this SDK is generated for the connector `default`. You can find more information about connectors in the [Data Connect documentation](https://firebase.google.com/docs/data-connect#how-does).

You can use this generated SDK by importing from the package `@tenderlens/dataconnect` as shown below. Both CommonJS and ESM imports are supported.

You can also follow the instructions from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#set-client).

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig } from '@tenderlens/dataconnect';

const dataConnect = getDataConnect(connectorConfig);
```

## Connecting to the local Emulator
By default, the connector will connect to the production service.

To connect to the emulator, you can use the following code.
You can also follow the emulator instructions from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#instrument-clients).

```typescript
import { connectDataConnectEmulator, getDataConnect } from 'firebase/data-connect';
import { connectorConfig } from '@tenderlens/dataconnect';

const dataConnect = getDataConnect(connectorConfig);
connectDataConnectEmulator(dataConnect, 'localhost', 9399);
```

After it's initialized, you can call your Data Connect [queries](#queries) and [mutations](#mutations) from your generated SDK.

# Queries

There are two ways to execute a Data Connect Query using the generated Web SDK:
- Using a Query Reference function, which returns a `QueryRef`
  - The `QueryRef` can be used as an argument to `executeQuery()`, which will execute the Query and return a `QueryPromise`
- Using an action shortcut function, which returns a `QueryPromise`
  - Calling the action shortcut function will execute the Query and return a `QueryPromise`

The following is true for both the action shortcut function and the `QueryRef` function:
- The `QueryPromise` returned will resolve to the result of the Query once it has finished executing
- If the Query accepts arguments, both the action shortcut function and the `QueryRef` function accept a single argument: an object that contains all the required variables (and the optional variables) for the Query
- Both functions can be called with or without passing in a `DataConnect` instance as an argument. If no `DataConnect` argument is passed in, then the generated SDK will call `getDataConnect(connectorConfig)` behind the scenes for you.

Below are examples of how to use the `default` connector's generated functions to execute each query. You can also follow the examples from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#using-queries).

## GetCurrentUser
You can execute the `GetCurrentUser` query using the following action shortcut function, or by calling `executeQuery()` after calling the following `QueryRef` function, both of which are defined in [dataconnect/index.d.ts](./index.d.ts):
```typescript
getCurrentUser(options?: ExecuteQueryOptions): QueryPromise<GetCurrentUserData, undefined>;

interface GetCurrentUserRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetCurrentUserData, undefined>;
}
export const getCurrentUserRef: GetCurrentUserRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `QueryRef` function.
```typescript
getCurrentUser(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<GetCurrentUserData, undefined>;

interface GetCurrentUserRef {
  ...
  (dc: DataConnect): QueryRef<GetCurrentUserData, undefined>;
}
export const getCurrentUserRef: GetCurrentUserRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the getCurrentUserRef:
```typescript
const name = getCurrentUserRef.operationName;
console.log(name);
```

### Variables
The `GetCurrentUser` query has no variables.
### Return Type
Recall that executing the `GetCurrentUser` query returns a `QueryPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `GetCurrentUserData`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface GetCurrentUserData {
  user?: {
    uid: string;
    email: string;
    displayName?: string | null;
    photoUrl?: string | null;
  } & User_Key;
}
```
### Using `GetCurrentUser`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, getCurrentUser } from '@tenderlens/dataconnect';


// Call the `getCurrentUser()` function to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await getCurrentUser();

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await getCurrentUser(dataConnect);

console.log(data.user);

// Or, you can use the `Promise` API.
getCurrentUser().then((response) => {
  const data = response.data;
  console.log(data.user);
});
```

### Using `GetCurrentUser`'s `QueryRef` function

```typescript
import { getDataConnect, executeQuery } from 'firebase/data-connect';
import { connectorConfig, getCurrentUserRef } from '@tenderlens/dataconnect';


// Call the `getCurrentUserRef()` function to get a reference to the query.
const ref = getCurrentUserRef();

// You can also pass in a `DataConnect` instance to the `QueryRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = getCurrentUserRef(dataConnect);

// Call `executeQuery()` on the reference to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeQuery(ref);

console.log(data.user);

// Or, you can use the `Promise` API.
executeQuery(ref).then((response) => {
  const data = response.data;
  console.log(data.user);
});
```

## GetMySupplierProfile
You can execute the `GetMySupplierProfile` query using the following action shortcut function, or by calling `executeQuery()` after calling the following `QueryRef` function, both of which are defined in [dataconnect/index.d.ts](./index.d.ts):
```typescript
getMySupplierProfile(options?: ExecuteQueryOptions): QueryPromise<GetMySupplierProfileData, undefined>;

interface GetMySupplierProfileRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetMySupplierProfileData, undefined>;
}
export const getMySupplierProfileRef: GetMySupplierProfileRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `QueryRef` function.
```typescript
getMySupplierProfile(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<GetMySupplierProfileData, undefined>;

interface GetMySupplierProfileRef {
  ...
  (dc: DataConnect): QueryRef<GetMySupplierProfileData, undefined>;
}
export const getMySupplierProfileRef: GetMySupplierProfileRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the getMySupplierProfileRef:
```typescript
const name = getMySupplierProfileRef.operationName;
console.log(name);
```

### Variables
The `GetMySupplierProfile` query has no variables.
### Return Type
Recall that executing the `GetMySupplierProfile` query returns a `QueryPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `GetMySupplierProfileData`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface GetMySupplierProfileData {
  supplierProfiles: ({
    id: UUIDString;
    companyName: string;
    categories: string[];
    turnoverLakhs?: number | null;
    turnoverYears?: number | null;
    maxEmdCapacityLakhs?: number | null;
    updatedAt: TimestampString;
  } & SupplierProfile_Key)[];
}
```
### Using `GetMySupplierProfile`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, getMySupplierProfile } from '@tenderlens/dataconnect';


// Call the `getMySupplierProfile()` function to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await getMySupplierProfile();

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await getMySupplierProfile(dataConnect);

console.log(data.supplierProfiles);

// Or, you can use the `Promise` API.
getMySupplierProfile().then((response) => {
  const data = response.data;
  console.log(data.supplierProfiles);
});
```

### Using `GetMySupplierProfile`'s `QueryRef` function

```typescript
import { getDataConnect, executeQuery } from 'firebase/data-connect';
import { connectorConfig, getMySupplierProfileRef } from '@tenderlens/dataconnect';


// Call the `getMySupplierProfileRef()` function to get a reference to the query.
const ref = getMySupplierProfileRef();

// You can also pass in a `DataConnect` instance to the `QueryRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = getMySupplierProfileRef(dataConnect);

// Call `executeQuery()` on the reference to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeQuery(ref);

console.log(data.supplierProfiles);

// Or, you can use the `Promise` API.
executeQuery(ref).then((response) => {
  const data = response.data;
  console.log(data.supplierProfiles);
});
```

## ListMySavedTenders
You can execute the `ListMySavedTenders` query using the following action shortcut function, or by calling `executeQuery()` after calling the following `QueryRef` function, both of which are defined in [dataconnect/index.d.ts](./index.d.ts):
```typescript
listMySavedTenders(options?: ExecuteQueryOptions): QueryPromise<ListMySavedTendersData, undefined>;

interface ListMySavedTendersRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<ListMySavedTendersData, undefined>;
}
export const listMySavedTendersRef: ListMySavedTendersRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `QueryRef` function.
```typescript
listMySavedTenders(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<ListMySavedTendersData, undefined>;

interface ListMySavedTendersRef {
  ...
  (dc: DataConnect): QueryRef<ListMySavedTendersData, undefined>;
}
export const listMySavedTendersRef: ListMySavedTendersRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the listMySavedTendersRef:
```typescript
const name = listMySavedTendersRef.operationName;
console.log(name);
```

### Variables
The `ListMySavedTenders` query has no variables.
### Return Type
Recall that executing the `ListMySavedTenders` query returns a `QueryPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `ListMySavedTendersData`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface ListMySavedTendersData {
  savedTenders: ({
    id: UUIDString;
    tenderRef: string;
    title: string;
    sourceUrl?: string | null;
    closingDate?: string | null;
    readinessStatus?: string | null;
    savedAt: TimestampString;
  } & SavedTender_Key)[];
}
```
### Using `ListMySavedTenders`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, listMySavedTenders } from '@tenderlens/dataconnect';


// Call the `listMySavedTenders()` function to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await listMySavedTenders();

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await listMySavedTenders(dataConnect);

console.log(data.savedTenders);

// Or, you can use the `Promise` API.
listMySavedTenders().then((response) => {
  const data = response.data;
  console.log(data.savedTenders);
});
```

### Using `ListMySavedTenders`'s `QueryRef` function

```typescript
import { getDataConnect, executeQuery } from 'firebase/data-connect';
import { connectorConfig, listMySavedTendersRef } from '@tenderlens/dataconnect';


// Call the `listMySavedTendersRef()` function to get a reference to the query.
const ref = listMySavedTendersRef();

// You can also pass in a `DataConnect` instance to the `QueryRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = listMySavedTendersRef(dataConnect);

// Call `executeQuery()` on the reference to execute the query.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeQuery(ref);

console.log(data.savedTenders);

// Or, you can use the `Promise` API.
executeQuery(ref).then((response) => {
  const data = response.data;
  console.log(data.savedTenders);
});
```

# Mutations

There are two ways to execute a Data Connect Mutation using the generated Web SDK:
- Using a Mutation Reference function, which returns a `MutationRef`
  - The `MutationRef` can be used as an argument to `executeMutation()`, which will execute the Mutation and return a `MutationPromise`
- Using an action shortcut function, which returns a `MutationPromise`
  - Calling the action shortcut function will execute the Mutation and return a `MutationPromise`

The following is true for both the action shortcut function and the `MutationRef` function:
- The `MutationPromise` returned will resolve to the result of the Mutation once it has finished executing
- If the Mutation accepts arguments, both the action shortcut function and the `MutationRef` function accept a single argument: an object that contains all the required variables (and the optional variables) for the Mutation
- Both functions can be called with or without passing in a `DataConnect` instance as an argument. If no `DataConnect` argument is passed in, then the generated SDK will call `getDataConnect(connectorConfig)` behind the scenes for you.

Below are examples of how to use the `default` connector's generated functions to execute each mutation. You can also follow the examples from the [Data Connect documentation](https://firebase.google.com/docs/data-connect/web-sdk#using-mutations).

## UpsertUser
You can execute the `UpsertUser` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect/index.d.ts](./index.d.ts):
```typescript
upsertUser(vars: UpsertUserVariables): MutationPromise<UpsertUserData, UpsertUserVariables>;

interface UpsertUserRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: UpsertUserVariables): MutationRef<UpsertUserData, UpsertUserVariables>;
}
export const upsertUserRef: UpsertUserRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
upsertUser(dc: DataConnect, vars: UpsertUserVariables): MutationPromise<UpsertUserData, UpsertUserVariables>;

interface UpsertUserRef {
  ...
  (dc: DataConnect, vars: UpsertUserVariables): MutationRef<UpsertUserData, UpsertUserVariables>;
}
export const upsertUserRef: UpsertUserRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the upsertUserRef:
```typescript
const name = upsertUserRef.operationName;
console.log(name);
```

### Variables
The `UpsertUser` mutation requires an argument of type `UpsertUserVariables`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface UpsertUserVariables {
  email: string;
  displayName?: string | null;
  photoUrl?: string | null;
}
```
### Return Type
Recall that executing the `UpsertUser` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `UpsertUserData`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface UpsertUserData {
  user_upsert: User_Key;
}
```
### Using `UpsertUser`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, upsertUser, UpsertUserVariables } from '@tenderlens/dataconnect';

// The `UpsertUser` mutation requires an argument of type `UpsertUserVariables`:
const upsertUserVars: UpsertUserVariables = {
  email: ..., 
  displayName: ..., // optional
  photoUrl: ..., // optional
};

// Call the `upsertUser()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await upsertUser(upsertUserVars);
// Variables can be defined inline as well.
const { data } = await upsertUser({ email: ..., displayName: ..., photoUrl: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await upsertUser(dataConnect, upsertUserVars);

console.log(data.user_upsert);

// Or, you can use the `Promise` API.
upsertUser(upsertUserVars).then((response) => {
  const data = response.data;
  console.log(data.user_upsert);
});
```

### Using `UpsertUser`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, upsertUserRef, UpsertUserVariables } from '@tenderlens/dataconnect';

// The `UpsertUser` mutation requires an argument of type `UpsertUserVariables`:
const upsertUserVars: UpsertUserVariables = {
  email: ..., 
  displayName: ..., // optional
  photoUrl: ..., // optional
};

// Call the `upsertUserRef()` function to get a reference to the mutation.
const ref = upsertUserRef(upsertUserVars);
// Variables can be defined inline as well.
const ref = upsertUserRef({ email: ..., displayName: ..., photoUrl: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = upsertUserRef(dataConnect, upsertUserVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.user_upsert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.user_upsert);
});
```

## CreateSupplierProfile
You can execute the `CreateSupplierProfile` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect/index.d.ts](./index.d.ts):
```typescript
createSupplierProfile(vars: CreateSupplierProfileVariables): MutationPromise<CreateSupplierProfileData, CreateSupplierProfileVariables>;

interface CreateSupplierProfileRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateSupplierProfileVariables): MutationRef<CreateSupplierProfileData, CreateSupplierProfileVariables>;
}
export const createSupplierProfileRef: CreateSupplierProfileRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
createSupplierProfile(dc: DataConnect, vars: CreateSupplierProfileVariables): MutationPromise<CreateSupplierProfileData, CreateSupplierProfileVariables>;

interface CreateSupplierProfileRef {
  ...
  (dc: DataConnect, vars: CreateSupplierProfileVariables): MutationRef<CreateSupplierProfileData, CreateSupplierProfileVariables>;
}
export const createSupplierProfileRef: CreateSupplierProfileRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the createSupplierProfileRef:
```typescript
const name = createSupplierProfileRef.operationName;
console.log(name);
```

### Variables
The `CreateSupplierProfile` mutation requires an argument of type `CreateSupplierProfileVariables`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface CreateSupplierProfileVariables {
  companyName: string;
  categories: string[];
  turnoverLakhs?: number | null;
  turnoverYears?: number | null;
  maxEmdCapacityLakhs?: number | null;
}
```
### Return Type
Recall that executing the `CreateSupplierProfile` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `CreateSupplierProfileData`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface CreateSupplierProfileData {
  supplierProfile_insert: SupplierProfile_Key;
}
```
### Using `CreateSupplierProfile`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, createSupplierProfile, CreateSupplierProfileVariables } from '@tenderlens/dataconnect';

// The `CreateSupplierProfile` mutation requires an argument of type `CreateSupplierProfileVariables`:
const createSupplierProfileVars: CreateSupplierProfileVariables = {
  companyName: ..., 
  categories: ..., 
  turnoverLakhs: ..., // optional
  turnoverYears: ..., // optional
  maxEmdCapacityLakhs: ..., // optional
};

// Call the `createSupplierProfile()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await createSupplierProfile(createSupplierProfileVars);
// Variables can be defined inline as well.
const { data } = await createSupplierProfile({ companyName: ..., categories: ..., turnoverLakhs: ..., turnoverYears: ..., maxEmdCapacityLakhs: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await createSupplierProfile(dataConnect, createSupplierProfileVars);

console.log(data.supplierProfile_insert);

// Or, you can use the `Promise` API.
createSupplierProfile(createSupplierProfileVars).then((response) => {
  const data = response.data;
  console.log(data.supplierProfile_insert);
});
```

### Using `CreateSupplierProfile`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, createSupplierProfileRef, CreateSupplierProfileVariables } from '@tenderlens/dataconnect';

// The `CreateSupplierProfile` mutation requires an argument of type `CreateSupplierProfileVariables`:
const createSupplierProfileVars: CreateSupplierProfileVariables = {
  companyName: ..., 
  categories: ..., 
  turnoverLakhs: ..., // optional
  turnoverYears: ..., // optional
  maxEmdCapacityLakhs: ..., // optional
};

// Call the `createSupplierProfileRef()` function to get a reference to the mutation.
const ref = createSupplierProfileRef(createSupplierProfileVars);
// Variables can be defined inline as well.
const ref = createSupplierProfileRef({ companyName: ..., categories: ..., turnoverLakhs: ..., turnoverYears: ..., maxEmdCapacityLakhs: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = createSupplierProfileRef(dataConnect, createSupplierProfileVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.supplierProfile_insert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.supplierProfile_insert);
});
```

## SaveTender
You can execute the `SaveTender` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect/index.d.ts](./index.d.ts):
```typescript
saveTender(vars: SaveTenderVariables): MutationPromise<SaveTenderData, SaveTenderVariables>;

interface SaveTenderRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: SaveTenderVariables): MutationRef<SaveTenderData, SaveTenderVariables>;
}
export const saveTenderRef: SaveTenderRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
saveTender(dc: DataConnect, vars: SaveTenderVariables): MutationPromise<SaveTenderData, SaveTenderVariables>;

interface SaveTenderRef {
  ...
  (dc: DataConnect, vars: SaveTenderVariables): MutationRef<SaveTenderData, SaveTenderVariables>;
}
export const saveTenderRef: SaveTenderRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the saveTenderRef:
```typescript
const name = saveTenderRef.operationName;
console.log(name);
```

### Variables
The `SaveTender` mutation requires an argument of type `SaveTenderVariables`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface SaveTenderVariables {
  tenderRef: string;
  title: string;
  sourceUrl?: string | null;
  closingDate?: string | null;
  readinessStatus?: string | null;
}
```
### Return Type
Recall that executing the `SaveTender` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `SaveTenderData`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface SaveTenderData {
  savedTender_insert: SavedTender_Key;
}
```
### Using `SaveTender`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, saveTender, SaveTenderVariables } from '@tenderlens/dataconnect';

// The `SaveTender` mutation requires an argument of type `SaveTenderVariables`:
const saveTenderVars: SaveTenderVariables = {
  tenderRef: ..., 
  title: ..., 
  sourceUrl: ..., // optional
  closingDate: ..., // optional
  readinessStatus: ..., // optional
};

// Call the `saveTender()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await saveTender(saveTenderVars);
// Variables can be defined inline as well.
const { data } = await saveTender({ tenderRef: ..., title: ..., sourceUrl: ..., closingDate: ..., readinessStatus: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await saveTender(dataConnect, saveTenderVars);

console.log(data.savedTender_insert);

// Or, you can use the `Promise` API.
saveTender(saveTenderVars).then((response) => {
  const data = response.data;
  console.log(data.savedTender_insert);
});
```

### Using `SaveTender`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, saveTenderRef, SaveTenderVariables } from '@tenderlens/dataconnect';

// The `SaveTender` mutation requires an argument of type `SaveTenderVariables`:
const saveTenderVars: SaveTenderVariables = {
  tenderRef: ..., 
  title: ..., 
  sourceUrl: ..., // optional
  closingDate: ..., // optional
  readinessStatus: ..., // optional
};

// Call the `saveTenderRef()` function to get a reference to the mutation.
const ref = saveTenderRef(saveTenderVars);
// Variables can be defined inline as well.
const ref = saveTenderRef({ tenderRef: ..., title: ..., sourceUrl: ..., closingDate: ..., readinessStatus: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = saveTenderRef(dataConnect, saveTenderVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.savedTender_insert);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.savedTender_insert);
});
```

## DeleteSavedTender
You can execute the `DeleteSavedTender` mutation using the following action shortcut function, or by calling `executeMutation()` after calling the following `MutationRef` function, both of which are defined in [dataconnect/index.d.ts](./index.d.ts):
```typescript
deleteSavedTender(vars: DeleteSavedTenderVariables): MutationPromise<DeleteSavedTenderData, DeleteSavedTenderVariables>;

interface DeleteSavedTenderRef {
  ...
  /* Allow users to create refs without passing in DataConnect */
  (vars: DeleteSavedTenderVariables): MutationRef<DeleteSavedTenderData, DeleteSavedTenderVariables>;
}
export const deleteSavedTenderRef: DeleteSavedTenderRef;
```
You can also pass in a `DataConnect` instance to the action shortcut function or `MutationRef` function.
```typescript
deleteSavedTender(dc: DataConnect, vars: DeleteSavedTenderVariables): MutationPromise<DeleteSavedTenderData, DeleteSavedTenderVariables>;

interface DeleteSavedTenderRef {
  ...
  (dc: DataConnect, vars: DeleteSavedTenderVariables): MutationRef<DeleteSavedTenderData, DeleteSavedTenderVariables>;
}
export const deleteSavedTenderRef: DeleteSavedTenderRef;
```

If you need the name of the operation without creating a ref, you can retrieve the operation name by calling the `operationName` property on the deleteSavedTenderRef:
```typescript
const name = deleteSavedTenderRef.operationName;
console.log(name);
```

### Variables
The `DeleteSavedTender` mutation requires an argument of type `DeleteSavedTenderVariables`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:

```typescript
export interface DeleteSavedTenderVariables {
  id: UUIDString;
}
```
### Return Type
Recall that executing the `DeleteSavedTender` mutation returns a `MutationPromise` that resolves to an object with a `data` property.

The `data` property is an object of type `DeleteSavedTenderData`, which is defined in [dataconnect/index.d.ts](./index.d.ts). It has the following fields:
```typescript
export interface DeleteSavedTenderData {
  savedTender_delete?: SavedTender_Key | null;
}
```
### Using `DeleteSavedTender`'s action shortcut function

```typescript
import { getDataConnect } from 'firebase/data-connect';
import { connectorConfig, deleteSavedTender, DeleteSavedTenderVariables } from '@tenderlens/dataconnect';

// The `DeleteSavedTender` mutation requires an argument of type `DeleteSavedTenderVariables`:
const deleteSavedTenderVars: DeleteSavedTenderVariables = {
  id: ..., 
};

// Call the `deleteSavedTender()` function to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await deleteSavedTender(deleteSavedTenderVars);
// Variables can be defined inline as well.
const { data } = await deleteSavedTender({ id: ..., });

// You can also pass in a `DataConnect` instance to the action shortcut function.
const dataConnect = getDataConnect(connectorConfig);
const { data } = await deleteSavedTender(dataConnect, deleteSavedTenderVars);

console.log(data.savedTender_delete);

// Or, you can use the `Promise` API.
deleteSavedTender(deleteSavedTenderVars).then((response) => {
  const data = response.data;
  console.log(data.savedTender_delete);
});
```

### Using `DeleteSavedTender`'s `MutationRef` function

```typescript
import { getDataConnect, executeMutation } from 'firebase/data-connect';
import { connectorConfig, deleteSavedTenderRef, DeleteSavedTenderVariables } from '@tenderlens/dataconnect';

// The `DeleteSavedTender` mutation requires an argument of type `DeleteSavedTenderVariables`:
const deleteSavedTenderVars: DeleteSavedTenderVariables = {
  id: ..., 
};

// Call the `deleteSavedTenderRef()` function to get a reference to the mutation.
const ref = deleteSavedTenderRef(deleteSavedTenderVars);
// Variables can be defined inline as well.
const ref = deleteSavedTenderRef({ id: ..., });

// You can also pass in a `DataConnect` instance to the `MutationRef` function.
const dataConnect = getDataConnect(connectorConfig);
const ref = deleteSavedTenderRef(dataConnect, deleteSavedTenderVars);

// Call `executeMutation()` on the reference to execute the mutation.
// You can use the `await` keyword to wait for the promise to resolve.
const { data } = await executeMutation(ref);

console.log(data.savedTender_delete);

// Or, you can use the `Promise` API.
executeMutation(ref).then((response) => {
  const data = response.data;
  console.log(data.savedTender_delete);
});
```

