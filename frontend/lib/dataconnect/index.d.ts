import { ConnectorConfig, DataConnect, QueryRef, QueryPromise, ExecuteQueryOptions, MutationRef, MutationPromise } from 'firebase/data-connect';

export const connectorConfig: ConnectorConfig;

export type TimestampString = string;
export type UUIDString = string;
export type Int64String = string;
export type DateString = string;




export interface CreateSupplierProfileData {
  supplierProfile_insert: SupplierProfile_Key;
}

export interface CreateSupplierProfileVariables {
  companyName: string;
  categories: string[];
  turnoverLakhs?: number | null;
  turnoverYears?: number | null;
  maxEmdCapacityLakhs?: number | null;
}

export interface DeleteSavedTenderData {
  savedTender_delete?: SavedTender_Key | null;
}

export interface DeleteSavedTenderVariables {
  id: UUIDString;
}

export interface GetCurrentUserData {
  user?: {
    uid: string;
    email: string;
    displayName?: string | null;
    photoUrl?: string | null;
  } & User_Key;
}

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

export interface SaveTenderData {
  savedTender_insert: SavedTender_Key;
}

export interface SaveTenderVariables {
  tenderRef: string;
  title: string;
  sourceUrl?: string | null;
  closingDate?: string | null;
  readinessStatus?: string | null;
}

export interface SavedTender_Key {
  id: UUIDString;
  __typename?: 'SavedTender_Key';
}

export interface SupplierProfile_Key {
  id: UUIDString;
  __typename?: 'SupplierProfile_Key';
}

export interface UpsertUserData {
  user_upsert: User_Key;
}

export interface UpsertUserVariables {
  email: string;
  displayName?: string | null;
  photoUrl?: string | null;
}

export interface User_Key {
  uid: string;
  __typename?: 'User_Key';
}

interface UpsertUserRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: UpsertUserVariables): MutationRef<UpsertUserData, UpsertUserVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: UpsertUserVariables): MutationRef<UpsertUserData, UpsertUserVariables>;
  operationName: string;
}
export const upsertUserRef: UpsertUserRef;

export function upsertUser(vars: UpsertUserVariables): MutationPromise<UpsertUserData, UpsertUserVariables>;
export function upsertUser(dc: DataConnect, vars: UpsertUserVariables): MutationPromise<UpsertUserData, UpsertUserVariables>;

interface CreateSupplierProfileRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: CreateSupplierProfileVariables): MutationRef<CreateSupplierProfileData, CreateSupplierProfileVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: CreateSupplierProfileVariables): MutationRef<CreateSupplierProfileData, CreateSupplierProfileVariables>;
  operationName: string;
}
export const createSupplierProfileRef: CreateSupplierProfileRef;

export function createSupplierProfile(vars: CreateSupplierProfileVariables): MutationPromise<CreateSupplierProfileData, CreateSupplierProfileVariables>;
export function createSupplierProfile(dc: DataConnect, vars: CreateSupplierProfileVariables): MutationPromise<CreateSupplierProfileData, CreateSupplierProfileVariables>;

interface SaveTenderRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: SaveTenderVariables): MutationRef<SaveTenderData, SaveTenderVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: SaveTenderVariables): MutationRef<SaveTenderData, SaveTenderVariables>;
  operationName: string;
}
export const saveTenderRef: SaveTenderRef;

export function saveTender(vars: SaveTenderVariables): MutationPromise<SaveTenderData, SaveTenderVariables>;
export function saveTender(dc: DataConnect, vars: SaveTenderVariables): MutationPromise<SaveTenderData, SaveTenderVariables>;

interface DeleteSavedTenderRef {
  /* Allow users to create refs without passing in DataConnect */
  (vars: DeleteSavedTenderVariables): MutationRef<DeleteSavedTenderData, DeleteSavedTenderVariables>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect, vars: DeleteSavedTenderVariables): MutationRef<DeleteSavedTenderData, DeleteSavedTenderVariables>;
  operationName: string;
}
export const deleteSavedTenderRef: DeleteSavedTenderRef;

export function deleteSavedTender(vars: DeleteSavedTenderVariables): MutationPromise<DeleteSavedTenderData, DeleteSavedTenderVariables>;
export function deleteSavedTender(dc: DataConnect, vars: DeleteSavedTenderVariables): MutationPromise<DeleteSavedTenderData, DeleteSavedTenderVariables>;

interface GetCurrentUserRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetCurrentUserData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<GetCurrentUserData, undefined>;
  operationName: string;
}
export const getCurrentUserRef: GetCurrentUserRef;

export function getCurrentUser(options?: ExecuteQueryOptions): QueryPromise<GetCurrentUserData, undefined>;
export function getCurrentUser(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<GetCurrentUserData, undefined>;

interface GetMySupplierProfileRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<GetMySupplierProfileData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<GetMySupplierProfileData, undefined>;
  operationName: string;
}
export const getMySupplierProfileRef: GetMySupplierProfileRef;

export function getMySupplierProfile(options?: ExecuteQueryOptions): QueryPromise<GetMySupplierProfileData, undefined>;
export function getMySupplierProfile(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<GetMySupplierProfileData, undefined>;

interface ListMySavedTendersRef {
  /* Allow users to create refs without passing in DataConnect */
  (): QueryRef<ListMySavedTendersData, undefined>;
  /* Allow users to pass in custom DataConnect instances */
  (dc: DataConnect): QueryRef<ListMySavedTendersData, undefined>;
  operationName: string;
}
export const listMySavedTendersRef: ListMySavedTendersRef;

export function listMySavedTenders(options?: ExecuteQueryOptions): QueryPromise<ListMySavedTendersData, undefined>;
export function listMySavedTenders(dc: DataConnect, options?: ExecuteQueryOptions): QueryPromise<ListMySavedTendersData, undefined>;

