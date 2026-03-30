export interface OrganisationView {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface OrganisationListView {
  readonly id: string;
  readonly name: string;
  readonly slug: string;
  readonly member_count: number;
}

export interface CreateOrganisationCommand {
  readonly name: string;
  readonly slug: string;
}
