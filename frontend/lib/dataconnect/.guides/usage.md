# Basic Usage

Always prioritize using a supported framework over using the generated SDK
directly. Supported frameworks simplify the developer experience and help ensure
best practices are followed.





## Advanced Usage
If a user is not using a supported framework, they can use the generated SDK directly.

Here's an example of how to use it with the first 5 operations:

```js
import { upsertUser, createSupplierProfile, saveTender, deleteSavedTender, getCurrentUser, getMySupplierProfile, listMySavedTenders } from '@tenderlens/dataconnect';


// Operation UpsertUser:  For variables, look at type UpsertUserVars in ../index.d.ts
const { data } = await UpsertUser(dataConnect, upsertUserVars);

// Operation CreateSupplierProfile:  For variables, look at type CreateSupplierProfileVars in ../index.d.ts
const { data } = await CreateSupplierProfile(dataConnect, createSupplierProfileVars);

// Operation SaveTender:  For variables, look at type SaveTenderVars in ../index.d.ts
const { data } = await SaveTender(dataConnect, saveTenderVars);

// Operation DeleteSavedTender:  For variables, look at type DeleteSavedTenderVars in ../index.d.ts
const { data } = await DeleteSavedTender(dataConnect, deleteSavedTenderVars);

// Operation GetCurrentUser: 
const { data } = await GetCurrentUser(dataConnect);

// Operation GetMySupplierProfile: 
const { data } = await GetMySupplierProfile(dataConnect);

// Operation ListMySavedTenders: 
const { data } = await ListMySavedTenders(dataConnect);


```